from __future__ import annotations

from types import SimpleNamespace

from torch_geometric.loader import DataLoader

from trail.gnn.train_gnn import GNNRegressor, record_to_graph


def test_gnn_architectures_forward_on_formula_graph() -> None:
    record = SimpleNamespace(smiles=["CCO", "NCC"], ratios=[0.4, 0.6], tg=42.0)
    graph = record_to_graph(record)
    assert graph is not None
    assert graph.edge_attr.shape[1] == 6
    batch = next(iter(DataLoader([graph], batch_size=1)))
    for architecture in ["gcn", "gin", "gat", "mpnn"]:
        model = GNNRegressor(architecture=architecture, hidden=32)
        pred = model(batch)
        assert pred.shape == (1,)
