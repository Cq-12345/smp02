from __future__ import annotations

import re
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import (
    AdaBoostRegressor,
    BaggingRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF as GPRRBF
from sklearn.kernel_ridge import KernelRidge
from sklearn.linear_model import ARDRegression, BayesianRidge, ElasticNet, HuberRegressor, Lasso, LinearRegression, Ridge, SGDRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import LinearSVR, NuSVR, SVR
from sklearn.tree import DecisionTreeRegressor
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm.auto import tqdm

from smp02.data import SMPRecord, unique_monomers
from smp02.utils import ensure_dir, save_json
from smp02.vae import encode_smiles, load_vae_checkpoint


class LatentCNNRegressor(nn.Module):
    def __init__(self, latent_size: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(1, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(256, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(128, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(64, 256),
            nn.ReLU(),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x.unsqueeze(1)).squeeze(-1)


def build_wvcm_features(records: Iterable[SMPRecord], vectors: dict[str, np.ndarray], latent_size: int) -> tuple[np.ndarray, np.ndarray]:
    features = []
    targets = []
    for rec in records:
        weighted = np.zeros(latent_size, dtype=np.float32)
        ok = True
        for smi, ratio in zip(rec.smiles, rec.ratios, strict=False):
            vec = vectors.get(smi)
            if vec is None:
                ok = False
                break
            weighted += float(ratio) * vec.astype(np.float32)
        if ok:
            features.append(weighted)
            targets.append(float(rec.tg))
    return np.vstack(features), np.asarray(targets, dtype=np.float32)


KELVIN_OFFSET = 273.15


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.maximum(np.abs(y_true), 1e-6)
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)


def mapek(y_true_celsius: np.ndarray, y_pred_celsius: np.ndarray) -> float:
    y_true_celsius = np.asarray(y_true_celsius, dtype=float)
    y_pred_celsius = np.asarray(y_pred_celsius, dtype=float)
    denom = np.maximum(y_true_celsius + KELVIN_OFFSET, 1e-6)
    return float(np.mean(np.abs(y_true_celsius - y_pred_celsius) / denom) * 100.0)


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def pcp(y_true: np.ndarray, y_pred: np.ndarray, tolerance: float = 0.15) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.maximum(np.abs(y_true), 1e-6)
    return float(np.mean((np.abs(y_true - y_pred) / denom) <= tolerance) * 100.0)


def regression_metrics(y_train: np.ndarray, pred_train: np.ndarray, y_test: np.ndarray, pred_test: np.ndarray, tolerance: float) -> dict[str, float]:
    return {
        "PCP training dataset (%)": pcp(y_train, pred_train, tolerance),
        "PCP test dataset (%)": pcp(y_test, pred_test, tolerance),
        "MAPE training dataset (%)": mape(y_train, pred_train),
        "MAPE test dataset (%)": mape(y_test, pred_test),
        "MAPEK training dataset (%)": mapek(y_train, pred_train),
        "MAPEK test dataset (%)": mapek(y_test, pred_test),
        "MAE training dataset (C)": mae(y_train, pred_train),
        "MAE test dataset (C)": mae(y_test, pred_test),
        "RMSE training dataset (C)": rmse(y_train, pred_train),
        "RMSE test dataset (C)": rmse(y_test, pred_test),
        "R2 training": float(r2_score(y_train, pred_train)),
        "R2 test": float(r2_score(y_test, pred_test)),
    }


def train_cnn_regressor(
    x_train: np.ndarray,
    y_train_scaled: np.ndarray,
    x_test: np.ndarray,
    latent_size: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    weight_decay: float,
    device: torch.device,
) -> tuple[LatentCNNRegressor, np.ndarray, np.ndarray, list[dict[str, float]]]:
    model = LatentCNNRegressor(latent_size).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    loss_fn = nn.MSELoss()
    dataset = TensorDataset(torch.from_numpy(x_train.astype(np.float32)), torch.from_numpy(y_train_scaled.astype(np.float32)))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    logs: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        total = 0.0
        batches = 0
        for xb, yb in tqdm(loader, desc=f"cnn latent={latent_size} epoch={epoch}/{epochs}", leave=False):
            xb = xb.to(device)
            yb = yb.to(device).view(-1)
            optimizer.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            optimizer.step()
            total += float(loss.detach())
            batches += 1
        logs.append({"epoch": float(epoch), "loss": total / max(batches, 1)})
    model.eval()
    with torch.no_grad():
        train_pred = model(torch.from_numpy(x_train.astype(np.float32)).to(device)).detach().cpu().numpy()
        test_pred = model(torch.from_numpy(x_test.astype(np.float32)).to(device)).detach().cpu().numpy()
    return model, train_pred, test_pred, logs


def safe_model_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_").lower()


def model_zoo_factories(pred_cfg: dict, seed: int, latent_size: int) -> list[tuple[str, Callable[[], object]]]:
    rf_large = int(pred_cfg.get("model_zoo_rf_large_estimators", 500))
    pls_small = max(1, min(2, latent_size))
    pls_medium = max(1, min(8, latent_size))
    factories: list[tuple[str, Callable[[], object]]] = [
        ("LinearRegression", lambda: LinearRegression()),
        ("Ridge_alpha_0.1", lambda: Ridge(alpha=0.1, random_state=seed)),
        ("Ridge_alpha_1", lambda: Ridge(alpha=1.0, random_state=seed)),
        ("Ridge_alpha_10", lambda: Ridge(alpha=10.0, random_state=seed)),
        ("Lasso_alpha_0.001", lambda: Lasso(alpha=0.001, random_state=seed, max_iter=10000)),
        ("ElasticNet_alpha_0.001_l1_0.2", lambda: ElasticNet(alpha=0.001, l1_ratio=0.2, random_state=seed, max_iter=10000)),
        ("ElasticNet_alpha_0.01_l1_0.5", lambda: ElasticNet(alpha=0.01, l1_ratio=0.5, random_state=seed, max_iter=10000)),
        ("BayesianRidge", lambda: BayesianRidge()),
        ("ARDRegression", lambda: ARDRegression()),
        ("HuberRegressor", lambda: HuberRegressor(max_iter=1000)),
        ("SGDRegressor_huber", lambda: SGDRegressor(loss="huber", random_state=seed, max_iter=3000, tol=1e-4)),
        ("SVR_RBF", lambda: SVR(C=float(pred_cfg["svr_c"]), epsilon=float(pred_cfg["svr_epsilon"]), kernel="rbf")),
        ("SVR_linear", lambda: SVR(C=100.0, epsilon=float(pred_cfg["svr_epsilon"]), kernel="linear")),
        ("SVR_poly2", lambda: SVR(C=100.0, epsilon=float(pred_cfg["svr_epsilon"]), kernel="poly", degree=2)),
        ("NuSVR_RBF", lambda: NuSVR(C=100.0, kernel="rbf", nu=0.4)),
        ("LinearSVR", lambda: LinearSVR(C=10.0, epsilon=0.01, random_state=seed, max_iter=10000)),
        ("KernelRidge_RBF_a1_gscale", lambda: KernelRidge(alpha=1.0, kernel="rbf", gamma=None)),
        ("KernelRidge_RBF_a0.1_g0.01", lambda: KernelRidge(alpha=0.1, kernel="rbf", gamma=0.01)),
        ("KernelRidge_linear", lambda: KernelRidge(alpha=1.0, kernel="linear")),
        ("KernelRidge_poly2", lambda: KernelRidge(alpha=1.0, kernel="poly", degree=2)),
        ("KNN_3_uniform", lambda: KNeighborsRegressor(n_neighbors=3, weights="uniform")),
        ("KNN_5_distance", lambda: KNeighborsRegressor(n_neighbors=5, weights="distance")),
        ("KNN_9_distance", lambda: KNeighborsRegressor(n_neighbors=9, weights="distance")),
        ("DecisionTree_depth_6", lambda: DecisionTreeRegressor(max_depth=6, random_state=seed)),
        ("RandomForest_paper", lambda: RandomForestRegressor(n_estimators=int(pred_cfg["rf_estimators"]), random_state=seed, n_jobs=-1)),
        ("RandomForest_large", lambda: RandomForestRegressor(n_estimators=rf_large, random_state=seed, n_jobs=-1)),
        ("ExtraTrees_300", lambda: ExtraTreesRegressor(n_estimators=300, random_state=seed, n_jobs=-1)),
        ("ExtraTrees_600", lambda: ExtraTreesRegressor(n_estimators=600, random_state=seed, n_jobs=-1)),
        ("GradientBoosting_squared", lambda: GradientBoostingRegressor(n_estimators=500, learning_rate=0.03, max_depth=3, random_state=seed)),
        ("GradientBoosting_huber", lambda: GradientBoostingRegressor(n_estimators=500, learning_rate=0.03, max_depth=3, loss="huber", random_state=seed)),
        ("HistGradientBoosting", lambda: HistGradientBoostingRegressor(max_iter=500, learning_rate=0.03, l2_regularization=0.01, random_state=seed)),
        ("AdaBoost_depth_4", lambda: AdaBoostRegressor(estimator=DecisionTreeRegressor(max_depth=4), n_estimators=300, learning_rate=0.03, random_state=seed)),
        ("BaggingTrees", lambda: BaggingRegressor(estimator=DecisionTreeRegressor(max_depth=8), n_estimators=200, random_state=seed, n_jobs=-1)),
        ("MLP_64", lambda: MLPRegressor(hidden_layer_sizes=(64,), activation="relu", solver="adam", alpha=1e-4, max_iter=2000, random_state=seed)),
        ("MLP_128_64", lambda: MLPRegressor(hidden_layer_sizes=(128, 64), activation="relu", solver="adam", alpha=1e-4, max_iter=2500, random_state=seed)),
        ("MLP_256_128_64", lambda: MLPRegressor(hidden_layer_sizes=(256, 128, 64), activation="relu", solver="adam", alpha=1e-4, max_iter=3000, random_state=seed)),
        ("PLS_2", lambda: PLSRegression(n_components=pls_small)),
        ("PLS_8", lambda: PLSRegression(n_components=pls_medium)),
        (
            "GaussianProcess_RBF",
            lambda: GaussianProcessRegressor(
                kernel=ConstantKernel(1.0) * GPRRBF(length_scale=1.0),
                alpha=1e-4,
                normalize_y=False,
                random_state=seed,
            ),
        ),
    ]
    try:
        from xgboost import XGBRegressor

        factories.extend(
            [
                (
                    "XGBoost_hist_depth3",
                    lambda: XGBRegressor(
                        n_estimators=600,
                        learning_rate=0.03,
                        max_depth=3,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        objective="reg:squarederror",
                        tree_method="hist",
                        n_jobs=-1,
                        random_state=seed,
                    ),
                ),
                (
                    "XGBoost_hist_depth5",
                    lambda: XGBRegressor(
                        n_estimators=500,
                        learning_rate=0.025,
                        max_depth=5,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        objective="reg:squarederror",
                        tree_method="hist",
                        n_jobs=-1,
                        random_state=seed,
                    ),
                ),
            ]
        )
    except Exception:
        pass
    try:
        from lightgbm import LGBMRegressor

        factories.extend(
            [
                (
                    "LightGBM_leaves31",
                    lambda: LGBMRegressor(
                        n_estimators=600,
                        learning_rate=0.03,
                        num_leaves=31,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        random_state=seed,
                        n_jobs=-1,
                        verbose=-1,
                    ),
                ),
                (
                    "LightGBM_leaves63",
                    lambda: LGBMRegressor(
                        n_estimators=500,
                        learning_rate=0.025,
                        num_leaves=63,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        random_state=seed,
                        n_jobs=-1,
                        verbose=-1,
                    ),
                ),
            ]
        )
    except Exception:
        pass
    try:
        from catboost import CatBoostRegressor

        factories.extend(
            [
                (
                    "CatBoost_depth6",
                    lambda: CatBoostRegressor(
                        iterations=600,
                        learning_rate=0.03,
                        depth=6,
                        loss_function="RMSE",
                        random_seed=seed,
                        verbose=False,
                        allow_writing_files=False,
                    ),
                ),
                (
                    "CatBoost_depth8",
                    lambda: CatBoostRegressor(
                        iterations=500,
                        learning_rate=0.025,
                        depth=8,
                        loss_function="RMSE",
                        random_seed=seed,
                        verbose=False,
                        allow_writing_files=False,
                    ),
                ),
            ]
        )
    except Exception:
        pass
    try:
        from ngboost import NGBRegressor

        factories.append(("NGBoost", lambda: NGBRegressor(n_estimators=400, learning_rate=0.03, verbose=False, random_state=seed)))
    except Exception:
        pass
    return factories


def fit_predict_scaled(model: object, x_train: np.ndarray, y_train_scaled: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(x_train, y_train_scaled)
    pred_train = np.asarray(model.predict(x_train)).reshape(-1)
    pred_test = np.asarray(model.predict(x_test)).reshape(-1)
    return pred_train, pred_test


def train_model_zoo(
    x_train_scaled: np.ndarray,
    y_train_scaled: np.ndarray,
    x_test_scaled: np.ndarray,
    x_scaler: MinMaxScaler,
    y_train: np.ndarray,
    y_test: np.ndarray,
    y_scaler: MinMaxScaler,
    latent_size: int,
    out: Path,
    cfg: dict,
) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    pred_cfg = cfg["predictors"]
    rows: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for name, factory in tqdm(model_zoo_factories(pred_cfg, int(cfg["seed"]), latent_size), desc=f"model zoo latent={latent_size}", leave=False):
        try:
            estimator = factory()
            pred_train_scaled, pred_test_scaled = fit_predict_scaled(estimator, x_train_scaled, y_train_scaled, x_test_scaled)
            pred_train = y_scaler.inverse_transform(pred_train_scaled.reshape(-1, 1)).ravel()
            pred_test = y_scaler.inverse_transform(pred_test_scaled.reshape(-1, 1)).ravel()
            metrics = regression_metrics(y_train, pred_train, y_test, pred_test, float(pred_cfg["pcp_tolerance"]))
            model_path = out / f"zoo_{safe_model_name(name)}_latent_{latent_size}.joblib"
            joblib.dump(
                {"model": estimator, "x_scaler": x_scaler, "y_scaler": y_scaler, "latent_size": latent_size},
                model_path,
            )
            rows.append(
                {
                    "ML method": f"VAE ({latent_size}) + {name}",
                    "latent_size": latent_size,
                    "model_family": "model_zoo",
                    "predictor_kind": "joblib",
                    "model_path": str(model_path),
                    **metrics,
                }
            )
        except Exception as exc:
            failures.append({"model": name, "error": repr(exc)})
    return rows, failures


def select_best_model(metrics_df: pd.DataFrame, out_dir: str | Path, cfg: dict) -> dict[str, object] | None:
    pred_cfg = cfg["predictors"]
    metric = str(pred_cfg.get("selection_metric", "R2 test"))
    higher = bool(pred_cfg.get("selection_higher_is_better", True))
    if metrics_df.empty or metric not in metrics_df.columns:
        return None
    eligible = metrics_df[metrics_df.get("model_path", "").astype(str).str.len() > 0].copy()
    eligible = eligible[eligible["predictor_kind"].astype(str).str.startswith("joblib")]
    eligible = eligible.replace([np.inf, -np.inf], np.nan).dropna(subset=[metric])
    if eligible.empty:
        return None
    best = eligible.sort_values(metric, ascending=not higher).iloc[0].to_dict()
    best["selection_metric"] = metric
    best["selection_higher_is_better"] = higher
    target = Path(out_dir)
    if target.suffix:
        save_json(best, target)
    else:
        save_json(best, target / "best_model.json")
    return best


def train_predictor_suite(
    records: list[SMPRecord],
    vae_checkpoint: str | Path,
    out_dir: str | Path,
    cfg: dict,
    device: torch.device,
) -> pd.DataFrame:
    out = ensure_dir(out_dir)
    model, checkpoint = load_vae_checkpoint(vae_checkpoint, map_location=device)
    model.to(device)
    latent_size = int(checkpoint["latent_size"])
    charset = checkpoint["charset"]
    max_length = int(checkpoint["max_length"])
    monomers = unique_monomers(records)
    latent = encode_smiles(model, monomers, charset, max_length, device=device, batch_size=cfg["vae"]["batch_size"])
    vector_map = {smi: latent[i] for i, smi in enumerate(monomers)}
    pd.DataFrame({"smiles": monomers, **{f"z_{i}": latent[:, i] for i in range(latent_size)}}).to_csv(
        out / f"monomer_vectors_latent_{latent_size}.csv", index=False
    )
    x, y = build_wvcm_features(records, vector_map, latent_size)
    np.savez(out / f"wvcm_features_latent_{latent_size}.npz", x=x, y=y)

    pred_cfg = cfg["predictors"]
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=float(pred_cfg["test_size"]),
        random_state=int(cfg["seed"]),
    )
    x_scaler = MinMaxScaler()
    y_scaler = MinMaxScaler()
    x_train_scaled = x_scaler.fit_transform(x_train)
    x_test_scaled = x_scaler.transform(x_test)
    y_train_scaled = y_scaler.fit_transform(y_train.reshape(-1, 1)).ravel()

    rows: list[dict[str, object]] = []

    svr = SVR(C=float(pred_cfg["svr_c"]), epsilon=float(pred_cfg["svr_epsilon"]), kernel=str(pred_cfg["svr_kernel"]))
    svr.fit(x_train_scaled, y_train_scaled)
    pred_train = y_scaler.inverse_transform(svr.predict(x_train_scaled).reshape(-1, 1)).ravel()
    pred_test = y_scaler.inverse_transform(svr.predict(x_test_scaled).reshape(-1, 1)).ravel()
    metrics = regression_metrics(y_train, pred_train, y_test, pred_test, float(pred_cfg["pcp_tolerance"]))
    svr_path = out / f"svr_latent_{latent_size}.joblib"
    rows.append(
        {
            "ML method": f"VAE ({latent_size}) + SVR",
            "latent_size": latent_size,
            "model_family": "paper",
            "predictor_kind": "joblib",
            "model_path": str(svr_path),
            **metrics,
        }
    )
    joblib.dump({"model": svr, "x_scaler": x_scaler, "y_scaler": y_scaler, "latent_size": latent_size}, svr_path)

    rf = RandomForestRegressor(n_estimators=int(pred_cfg["rf_estimators"]), random_state=int(cfg["seed"]), n_jobs=-1)
    rf.fit(x_train_scaled, y_train_scaled)
    pred_train = y_scaler.inverse_transform(rf.predict(x_train_scaled).reshape(-1, 1)).ravel()
    pred_test = y_scaler.inverse_transform(rf.predict(x_test_scaled).reshape(-1, 1)).ravel()
    metrics = regression_metrics(y_train, pred_train, y_test, pred_test, float(pred_cfg["pcp_tolerance"]))
    rf_path = out / f"rf_latent_{latent_size}.joblib"
    rows.append(
        {
            "ML method": f"VAE ({latent_size}) + RF",
            "latent_size": latent_size,
            "model_family": "paper",
            "predictor_kind": "joblib",
            "model_path": str(rf_path),
            **metrics,
        }
    )
    joblib.dump({"model": rf, "x_scaler": x_scaler, "y_scaler": y_scaler, "latent_size": latent_size}, rf_path)

    cnn, cnn_train_scaled, cnn_test_scaled, logs = train_cnn_regressor(
        x_train_scaled,
        y_train_scaled,
        x_test_scaled,
        latent_size=latent_size,
        epochs=int(pred_cfg["cnn_epochs"]),
        batch_size=int(pred_cfg["cnn_batch_size"]),
        learning_rate=float(pred_cfg["cnn_learning_rate"]),
        weight_decay=float(pred_cfg["cnn_weight_decay"]),
        device=device,
    )
    pred_train = y_scaler.inverse_transform(cnn_train_scaled.reshape(-1, 1)).ravel()
    pred_test = y_scaler.inverse_transform(cnn_test_scaled.reshape(-1, 1)).ravel()
    metrics = regression_metrics(y_train, pred_train, y_test, pred_test, float(pred_cfg["pcp_tolerance"]))
    cnn_path = out / f"cnn_latent_{latent_size}.pt"
    rows.append(
        {
            "ML method": f"VAE ({latent_size}) + CNN",
            "latent_size": latent_size,
            "model_family": "paper",
            "predictor_kind": "torch_cnn",
            "model_path": str(cnn_path),
            **metrics,
        }
    )
    torch.save({"state_dict": cnn.state_dict(), "latent_size": latent_size, "logs": logs}, cnn_path)
    joblib.dump({"x_scaler": x_scaler, "y_scaler": y_scaler, "latent_size": latent_size}, out / f"cnn_scalers_latent_{latent_size}.joblib")

    zoo_rows, failures = train_model_zoo(
        x_train_scaled,
        y_train_scaled,
        x_test_scaled,
        x_scaler,
        y_train,
        y_test,
        y_scaler,
        latent_size,
        out,
        cfg,
    )
    rows.extend(zoo_rows)
    if failures:
        pd.DataFrame(failures).to_csv(out / f"model_zoo_failures_latent_{latent_size}.csv", index=False)

    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv(out / f"predictor_metrics_latent_{latent_size}.csv", index=False)
    select_best_model(metrics_df, out / f"best_model_latent_{latent_size}.json", cfg)
    return metrics_df


def load_predictor(path: str | Path) -> dict:
    return joblib.load(path)


def predict_sklearn_bundle(bundle: dict, x: np.ndarray) -> np.ndarray:
    x_scaled = bundle["x_scaler"].transform(x)
    y_scaled = bundle["model"].predict(x_scaled)
    return bundle["y_scaler"].inverse_transform(y_scaled.reshape(-1, 1)).ravel()
