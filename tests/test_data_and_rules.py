from smp02.data import parse_ratios, parse_smiles_set
from smp02.discovery import ratio_grid
from smp02.functional_groups import classify_smiles, is_reasonable_pair


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

