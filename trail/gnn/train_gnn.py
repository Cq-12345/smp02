from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from rdkit import Chem
from rdkit.Chem import Descriptors
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from torch import nn
from torch.nn import functional as F
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GATConv, GCNConv, GINConv, NNConv, global_mean_pool

from smp02.data import load_smp_records
from smp02.functional_groups import SMARTS, classify_smiles, compatibility_reason


KELVIN_OFFSET = 273.15
GROUP_NAMES = tuple(SMARTS.keys())
REACTIVE_GROUPS = frozenset(
    {
        "epoxy",
        "primary_amine",
        "secondary_amine",
        "anhydride",
        "isocyanate",
        "hydroxyl",
        "phenol",
        "carboxylic_acid",
        "acrylate_or_methacrylate",
        "vinyl",
        "thiol",
        "cyanate_ester",
        "maleimide",
    }
)
FORMULATION_GLOBAL_FEATURE_DIM = 31


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float))))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mapek(y_true_c: np.ndarray, y_pred_c: np.ndarray) -> float:
    y_true_c = np.asarray(y_true_c, dtype=float)
    y_pred_c = np.asarray(y_pred_c, dtype=float)
    denom = np.maximum(y_true_c + KELVIN_OFFSET, 1e-6)
    return float(np.mean(np.abs(y_true_c - y_pred_c) / denom) * 100.0)


def pcp(y_true: np.ndarray, y_pred: np.ndarray, tolerance: float = 0.15) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.maximum(np.abs(y_true), 1e-6)
    return float(np.mean((np.abs(y_true - y_pred) / denom) <= tolerance) * 100.0)


def regression_metrics(y_train: np.ndarray, p_train: np.ndarray, y_test: np.ndarray, p_test: np.ndarray) -> dict[str, float]:
    return {
        "MAPEK training dataset (%)": mapek(y_train, p_train),
        "MAPEK test dataset (%)": mapek(y_test, p_test),
        "MAE training dataset (C)": mae(y_train, p_train),
        "MAE test dataset (C)": mae(y_test, p_test),
        "RMSE training dataset (C)": rmse(y_train, p_train),
        "RMSE test dataset (C)": rmse(y_test, p_test),
        "PCP training dataset (%)": pcp(y_train, p_train),
        "PCP test dataset (%)": pcp(y_test, p_test),
        "R2 training": float(r2_score(y_train, p_train)),
        "R2 test": float(r2_score(y_test, p_test)),
    }


def atom_features(atom: Chem.Atom, ratio: float) -> list[float]:
    return [
        atom.GetAtomicNum() / 100.0,
        atom.GetDegree() / 6.0,
        atom.GetFormalCharge() / 4.0,
        float(atom.GetIsAromatic()),
        ratio,
    ]


def bond_features(bond: Chem.Bond) -> list[float]:
    bond_type = bond.GetBondType()
    return [
        float(bond_type == Chem.BondType.SINGLE),
        float(bond_type == Chem.BondType.DOUBLE),
        float(bond_type == Chem.BondType.TRIPLE),
        float(bond_type == Chem.BondType.AROMATIC),
        float(bond.GetIsConjugated()),
        float(bond.IsInRing()),
    ]


def formulation_global_features(smiles: tuple[str, ...] | list[str], ratios: tuple[float, ...] | list[float], mols: list[Chem.Mol] | None = None) -> list[float]:
    ratios_array = np.asarray(ratios, dtype=float)
    total = float(ratios_array.sum())
    if total <= 0:
        ratios_array = np.full(len(smiles), 1.0 / max(len(smiles), 1), dtype=float)
    else:
        ratios_array = ratios_array / total
    if mols is None:
        mols = [Chem.MolFromSmiles(smi) for smi in smiles]
    valid_mols = [mol for mol in mols if mol is not None]
    if not smiles or not valid_mols:
        return [0.0] * FORMULATION_GLOBAL_FEATURE_DIM

    entropy = float(-(ratios_array * np.log(np.maximum(ratios_array, 1e-12))).sum())
    entropy_norm = entropy / max(np.log(max(len(ratios_array), 2)), 1e-12)
    ratio_features = [
        min(len(smiles) / 4.0, 1.0),
        float(ratios_array.max()),
        float(ratios_array.min()),
        float(ratios_array.std()),
        float(entropy_norm),
    ]

    heavy_atoms = []
    aromatic_fractions = []
    hetero_fractions = []
    ring_counts = []
    rotatable_bonds = []
    group_sets = []
    for smi, mol in zip(smiles, mols, strict=False):
        if mol is None:
            group_sets.append(set())
            heavy_atoms.append(0.0)
            aromatic_fractions.append(0.0)
            hetero_fractions.append(0.0)
            ring_counts.append(0.0)
            rotatable_bonds.append(0.0)
            continue
        heavy = max(float(mol.GetNumHeavyAtoms()), 1.0)
        aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
        hetero_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() not in {1, 6})
        heavy_atoms.append(heavy)
        aromatic_fractions.append(float(aromatic_atoms) / heavy)
        hetero_fractions.append(float(hetero_atoms) / heavy)
        ring_counts.append(float(mol.GetRingInfo().NumRings()))
        rotatable_bonds.append(float(Descriptors.NumRotatableBonds(mol)))
        group_sets.append(set(classify_smiles(smi).groups))
    descriptor_features = [
        float(np.dot(ratios_array, np.asarray(heavy_atoms))) / 100.0,
        float(np.dot(ratios_array, np.asarray(aromatic_fractions))),
        float(np.dot(ratios_array, np.asarray(hetero_fractions))),
        float(np.dot(ratios_array, np.asarray(ring_counts))) / 10.0,
        float(np.dot(ratios_array, np.asarray(rotatable_bonds))) / 20.0,
    ]

    group_features = []
    for group_name in GROUP_NAMES:
        group_features.append(float(sum(ratio for ratio, groups in zip(ratios_array, group_sets, strict=False) if group_name in groups)))

    compatible_pairs = 0
    possible_pairs = 0
    for idx, groups_a in enumerate(group_sets):
        for groups_b in group_sets[idx + 1 :]:
            possible_pairs += 1
            if compatibility_reason(groups_a, groups_b):
                compatible_pairs += 1
    compatible_fraction = float(compatible_pairs / possible_pairs) if possible_pairs else 0.0
    reactive_weight = float(sum(ratio for ratio, groups in zip(ratios_array, group_sets, strict=False) if groups & REACTIVE_GROUPS))
    compatibility_features = [float(compatible_pairs > 0), compatible_fraction, reactive_weight]

    features = ratio_features + descriptor_features + group_features + compatibility_features
    if len(features) != FORMULATION_GLOBAL_FEATURE_DIM:
        raise AssertionError(f"Expected {FORMULATION_GLOBAL_FEATURE_DIM} global features, got {len(features)}")
    return features


def record_to_graph(record, include_global_features: bool = False) -> Data | None:
    xs = []
    edges = []
    edge_attrs = []
    mols = []
    offset = 0
    for smi, ratio in zip(record.smiles, record.ratios, strict=False):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            return None
        mols.append(mol)
        for atom in mol.GetAtoms():
            xs.append(atom_features(atom, float(ratio)))
        for bond in mol.GetBonds():
            a = offset + bond.GetBeginAtomIdx()
            b = offset + bond.GetEndAtomIdx()
            attrs = bond_features(bond)
            edges.append([a, b])
            edges.append([b, a])
            edge_attrs.append(attrs)
            edge_attrs.append(attrs)
        offset += mol.GetNumAtoms()
    if not xs:
        return None
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous() if edges else torch.empty((2, 0), dtype=torch.long)
    edge_attr = torch.tensor(edge_attrs, dtype=torch.float32) if edge_attrs else torch.empty((0, 6), dtype=torch.float32)
    data = Data(x=torch.tensor(xs, dtype=torch.float32), edge_index=edge_index, edge_attr=edge_attr, y=torch.tensor([record.tg], dtype=torch.float32))
    if include_global_features:
        data.global_x = torch.tensor([formulation_global_features(record.smiles, record.ratios, mols)], dtype=torch.float32)
    return data


class GNNRegressor(nn.Module):
    def __init__(self, in_channels: int = 5, hidden: int = 64, edge_channels: int = 6, architecture: str = "gcn", global_channels: int = 0) -> None:
        super().__init__()
        self.architecture = architecture.lower()
        self.global_channels = int(global_channels)
        if self.architecture == "gcn":
            self.conv1 = GCNConv(in_channels, hidden)
            self.conv2 = GCNConv(hidden, hidden)
        elif self.architecture == "gin":
            self.conv1 = GINConv(nn.Sequential(nn.Linear(in_channels, hidden), nn.ReLU(), nn.Linear(hidden, hidden)))
            self.conv2 = GINConv(nn.Sequential(nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, hidden)))
        elif self.architecture == "gat":
            heads = 4
            self.conv1 = GATConv(in_channels, hidden // heads, heads=heads, concat=True)
            self.conv2 = GATConv(hidden, hidden // heads, heads=heads, concat=True)
        elif self.architecture == "mpnn":
            self.edge_mlp1 = nn.Sequential(nn.Linear(edge_channels, hidden), nn.ReLU(), nn.Linear(hidden, in_channels * hidden))
            self.edge_mlp2 = nn.Sequential(nn.Linear(edge_channels, hidden), nn.ReLU(), nn.Linear(hidden, hidden * hidden))
            self.conv1 = NNConv(in_channels, hidden, self.edge_mlp1, aggr="mean")
            self.conv2 = NNConv(hidden, hidden, self.edge_mlp2, aggr="mean")
        else:
            raise ValueError(f"Unknown GNN architecture: {architecture}")
        self.head = nn.Sequential(nn.Linear(hidden + self.global_channels, hidden), nn.ReLU(), nn.Linear(hidden, 1))

    def forward(self, data: Data) -> torch.Tensor:
        if self.architecture == "mpnn":
            x = F.relu(self.conv1(data.x, data.edge_index, data.edge_attr))
            x = F.relu(self.conv2(x, data.edge_index, data.edge_attr))
        else:
            x = F.relu(self.conv1(data.x, data.edge_index))
            x = F.relu(self.conv2(x, data.edge_index))
        pooled = global_mean_pool(x, data.batch)
        if self.global_channels:
            global_x = getattr(data, "global_x", None)
            if global_x is None:
                global_x = pooled.new_zeros((pooled.shape[0], self.global_channels))
            if global_x.dim() == 1:
                global_x = global_x.view(pooled.shape[0], self.global_channels)
            pooled = torch.cat([pooled, global_x.to(pooled.device)], dim=1)
        return self.head(pooled).view(-1)


def cpu_state_dict(model: nn.Module) -> dict[str, torch.Tensor]:
    return {key: value.detach().cpu() for key, value in model.state_dict().items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/SMP_Dataset.xlsx")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--architecture", choices=["gcn", "gin", "gat", "mpnn"], default="gcn")
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--test-size", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--global-features", action="store_true", help="Concatenate formulation-level descriptors, functional-group weights, and reaction compatibility features after graph pooling.")
    parser.add_argument("--out", default="artifacts/trail/gnn")
    args = parser.parse_args()
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    records = load_smp_records(args.data)
    graphs = [g for g in (record_to_graph(r, include_global_features=args.global_features) for r in records) if g is not None]
    train_graphs, test_graphs = train_test_split(graphs, test_size=args.test_size, random_state=args.seed)
    train_loader = DataLoader(train_graphs, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_graphs, batch_size=args.batch_size)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    global_channels = FORMULATION_GLOBAL_FEATURE_DIM if args.global_features else 0
    model = GNNRegressor(hidden=args.hidden, architecture=args.architecture, global_channels=global_channels).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    loss_history = []
    for _ in range(args.epochs):
        model.train()
        epoch_loss = 0.0
        n_batches = 0
        for batch in train_loader:
            batch = batch.to(device)
            opt.zero_grad(set_to_none=True)
            pred = model(batch)
            loss = F.mse_loss(pred, batch.y.view(-1))
            loss.backward()
            opt.step()
            epoch_loss += float(loss.detach().cpu())
            n_batches += 1
        loss_history.append(epoch_loss / max(n_batches, 1))
    def predict(loader):
        ys, ps = [], []
        model.eval()
        with torch.no_grad():
            for batch in loader:
                batch = batch.to(device)
                ys.extend(batch.y.view(-1).detach().cpu().numpy().tolist())
                ps.extend(model(batch).detach().cpu().numpy().tolist())
        return np.asarray(ys), np.asarray(ps)
    y_train, p_train = predict(train_loader)
    y_test, p_test = predict(test_loader)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    torch.save(cpu_state_dict(model), out / f"gnn_{args.architecture}_tg_regressor.pt")
    metrics = regression_metrics(y_train, p_train, y_test, p_test)
    metrics.update(
        {
            "ML method": f"SmallMoleculeGraph{args.architecture.upper()}",
            "model_family": "gnn",
            "architecture": args.architecture,
            "global_features": bool(args.global_features),
            "global_feature_dim": int(global_channels),
            "hidden": int(args.hidden),
            "epochs": int(args.epochs),
            "batch_size": int(args.batch_size),
            "test_size": float(args.test_size),
            "seed": int(args.seed),
            "n_graphs": int(len(graphs)),
            "n_train": int(len(train_graphs)),
            "n_test": int(len(test_graphs)),
            "final_train_loss": float(loss_history[-1]) if loss_history else None,
        }
    )
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame([metrics]).to_csv(out / "metrics.csv", index=False)
    pd.DataFrame({"split": "train", "y_true": y_train, "y_pred": p_train}).to_csv(out / "train_predictions.csv", index=False)
    pd.DataFrame({"split": "test", "y_true": y_test, "y_pred": p_test}).to_csv(out / "test_predictions.csv", index=False)


if __name__ == "__main__":
    main()
