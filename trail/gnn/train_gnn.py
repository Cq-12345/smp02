from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
from rdkit import Chem
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from torch import nn
from torch.nn import functional as F
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GCNConv, global_mean_pool

from smp02.data import load_smp_records


def atom_features(atom: Chem.Atom, ratio: float) -> list[float]:
    return [
        atom.GetAtomicNum() / 100.0,
        atom.GetDegree() / 6.0,
        atom.GetFormalCharge() / 4.0,
        float(atom.GetIsAromatic()),
        ratio,
    ]


def record_to_graph(record) -> Data | None:
    xs = []
    edges = []
    offset = 0
    for smi, ratio in zip(record.smiles, record.ratios, strict=False):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            return None
        for atom in mol.GetAtoms():
            xs.append(atom_features(atom, float(ratio)))
        for bond in mol.GetBonds():
            a = offset + bond.GetBeginAtomIdx()
            b = offset + bond.GetEndAtomIdx()
            edges.append([a, b])
            edges.append([b, a])
        offset += mol.GetNumAtoms()
    if not xs:
        return None
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous() if edges else torch.empty((2, 0), dtype=torch.long)
    return Data(x=torch.tensor(xs, dtype=torch.float32), edge_index=edge_index, y=torch.tensor([record.tg], dtype=torch.float32))


class GNNRegressor(nn.Module):
    def __init__(self, in_channels: int = 5, hidden: int = 64) -> None:
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden)
        self.conv2 = GCNConv(hidden, hidden)
        self.head = nn.Sequential(nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, 1))

    def forward(self, data: Data) -> torch.Tensor:
        x = F.relu(self.conv1(data.x, data.edge_index))
        x = F.relu(self.conv2(x, data.edge_index))
        pooled = global_mean_pool(x, data.batch)
        return self.head(pooled).view(-1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/SMP_Dataset.xlsx")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--out", default="artifacts/trail/gnn")
    args = parser.parse_args()
    records = load_smp_records(args.data)
    graphs = [g for g in (record_to_graph(r) for r in records) if g is not None]
    train_graphs, test_graphs = train_test_split(graphs, test_size=0.15, random_state=42)
    train_loader = DataLoader(train_graphs, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_graphs, batch_size=args.batch_size)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = GNNRegressor().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    for _ in range(args.epochs):
        model.train()
        for batch in train_loader:
            batch = batch.to(device)
            opt.zero_grad(set_to_none=True)
            pred = model(batch)
            loss = F.mse_loss(pred, batch.y.view(-1))
            loss.backward()
            opt.step()
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
    torch.save(model.state_dict(), out / "gnn_tg_regressor.pt")
    (out / "metrics.json").write_text(
        '{"r2_train": %.6f, "r2_test": %.6f}' % (r2_score(y_train, p_train), r2_score(y_test, p_test)),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

