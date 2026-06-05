from __future__ import annotations

from types import SimpleNamespace

from torch_geometric.loader import DataLoader

from trail.gnn.train_gnn import FORMULATION_GLOBAL_FEATURE_DIM, GNNRegressor, formulation_global_features, record_to_graph


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


def test_gnn_global_features_batch_and_forward() -> None:
    record = SimpleNamespace(
        smiles=["CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1", "NCCN"],
        ratios=[0.45, 0.55],
        tg=155.0,
    )
    features = formulation_global_features(record.smiles, record.ratios)
    assert len(features) == FORMULATION_GLOBAL_FEATURE_DIM
    assert features[-3] == 1.0
    graph = record_to_graph(record, include_global_features=True)
    assert graph is not None
    assert graph.global_x.shape == (1, FORMULATION_GLOBAL_FEATURE_DIM)
    batch = next(iter(DataLoader([graph, graph], batch_size=2)))
    assert batch.global_x.shape == (2, FORMULATION_GLOBAL_FEATURE_DIM)
    model = GNNRegressor(architecture="mpnn", hidden=32, global_channels=FORMULATION_GLOBAL_FEATURE_DIM)
    pred = model(batch)
    assert pred.shape == (2,)
