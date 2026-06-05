from smp02.data import parse_ratios, parse_smiles_set
from smp02.discovery import ratio_grid
from smp02.functional_groups import classify_smiles, is_reasonable_pair
from smp02.predictors import mae, mape, mapek, rmse


def test_parse_smiles_set_and_ratios() -> None:
    smiles = parse_smiles_set("{CCO, NCC}")
    assert smiles == ["CCO", "NCC"]
    ratios = parse_ratios("0.25:0.75", 2)
    assert ratios == [0.25, 0.75]


def test_ratio_grid() -> None:
    assert ratio_grid(0.05, 0.25, 0.10) == [0.05, 0.15, 0.25]


def test_functional_group_classification() -> None:
    result = classify_smiles("NCCN")
    assert "primary_amine" in result.groups


def test_reasonable_pair_epoxy_amine() -> None:
    ok, reason = is_reasonable_pair("C1CO1", "NCCN")
    assert ok
    assert "环氧" in reason


def test_temperature_metrics_keep_celsius_mape_and_add_kelvin_mape() -> None:
    y_true = [-2.0, 0.5, 100.0]
    y_pred = [-1.0, 1.5, 110.0]

    assert round(mape(y_true, y_pred), 6) == 86.666667
    assert round(mapek(y_true, y_pred), 6) == 1.138039
    assert mae(y_true, y_pred) == 4.0
    assert round(rmse(y_true, y_pred), 6) == 5.830952
