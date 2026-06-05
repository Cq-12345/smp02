from __future__ import annotations

from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVR
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm.auto import tqdm

from smp02.data import SMPRecord, unique_monomers
from smp02.utils import ensure_dir
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


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.maximum(np.abs(y_true), 1e-6)
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)


def pcp(y_true: np.ndarray, y_pred: np.ndarray, tolerance: float = 0.15) -> float:
    denom = np.maximum(np.abs(y_true), 1e-6)
    return float(np.mean((np.abs(y_true - y_pred) / denom) <= tolerance) * 100.0)


def regression_metrics(y_train: np.ndarray, pred_train: np.ndarray, y_test: np.ndarray, pred_test: np.ndarray, tolerance: float) -> dict[str, float]:
    return {
        "PCP training dataset (%)": pcp(y_train, pred_train, tolerance),
        "PCP test dataset (%)": pcp(y_test, pred_test, tolerance),
        "MAPE training dataset (%)": mape(y_train, pred_train),
        "MAPE test dataset (%)": mape(y_test, pred_test),
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

    rows = []

    svr = SVR(C=float(pred_cfg["svr_c"]), epsilon=float(pred_cfg["svr_epsilon"]), kernel=str(pred_cfg["svr_kernel"]))
    svr.fit(x_train_scaled, y_train_scaled)
    pred_train = y_scaler.inverse_transform(svr.predict(x_train_scaled).reshape(-1, 1)).ravel()
    pred_test = y_scaler.inverse_transform(svr.predict(x_test_scaled).reshape(-1, 1)).ravel()
    metrics = regression_metrics(y_train, pred_train, y_test, pred_test, float(pred_cfg["pcp_tolerance"]))
    rows.append({"ML method": f"VAE ({latent_size}) + SVR", **metrics})
    joblib.dump({"model": svr, "x_scaler": x_scaler, "y_scaler": y_scaler, "latent_size": latent_size}, out / f"svr_latent_{latent_size}.joblib")

    rf = RandomForestRegressor(n_estimators=int(pred_cfg["rf_estimators"]), random_state=int(cfg["seed"]), n_jobs=-1)
    rf.fit(x_train_scaled, y_train_scaled)
    pred_train = y_scaler.inverse_transform(rf.predict(x_train_scaled).reshape(-1, 1)).ravel()
    pred_test = y_scaler.inverse_transform(rf.predict(x_test_scaled).reshape(-1, 1)).ravel()
    metrics = regression_metrics(y_train, pred_train, y_test, pred_test, float(pred_cfg["pcp_tolerance"]))
    rows.append({"ML method": f"VAE ({latent_size}) + RF", **metrics})
    joblib.dump({"model": rf, "x_scaler": x_scaler, "y_scaler": y_scaler, "latent_size": latent_size}, out / f"rf_latent_{latent_size}.joblib")

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
    rows.append({"ML method": f"VAE ({latent_size}) + CNN", **metrics})
    torch.save({"state_dict": cnn.state_dict(), "latent_size": latent_size, "logs": logs}, out / f"cnn_latent_{latent_size}.pt")
    joblib.dump({"x_scaler": x_scaler, "y_scaler": y_scaler, "latent_size": latent_size}, out / f"cnn_scalers_latent_{latent_size}.joblib")

    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv(out / f"predictor_metrics_latent_{latent_size}.csv", index=False)
    return metrics_df


def load_predictor(path: str | Path) -> dict:
    return joblib.load(path)


def predict_sklearn_bundle(bundle: dict, x: np.ndarray) -> np.ndarray:
    x_scaled = bundle["x_scaler"].transform(x)
    y_scaled = bundle["model"].predict(x_scaled)
    return bundle["y_scaler"].inverse_transform(y_scaled.reshape(-1, 1)).ravel()

