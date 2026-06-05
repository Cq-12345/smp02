from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rdkit import Chem
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")


SMARTS: dict[str, str] = {
    "epoxy": "[#6]1-[#8]-[#6]1",
    "primary_amine": "[NX3;H2][#6]",
    "secondary_amine": "[NX3;H1]([#6])[#6]",
    "anhydride": "[CX3](=O)[OX2][CX3](=O)",
    "isocyanate": "[NX2]=[CX2]=[OX1]",
    "hydroxyl": "[OX2H][#6]",
    "phenol": "[OX2H]c",
    "carboxylic_acid": "[CX3](=O)[OX2H1]",
    "ester": "[CX3](=O)[OX2][#6]",
    "ether": "[OD2]([#6])[#6]",
    "acrylate_or_methacrylate": "[CX3](=O)[OX2][#6][CX3]=[CX3]",
    "vinyl": "[CX3]=[CX3]",
    "thiol": "[SX2H]",
    "cyanate_ester": "[OX2][CX2]#[NX1]",
    "nitrile": "[CX2]#[NX1]",
    "maleimide": "O=C1NC(=O)C=C1",
    "imide": "[CX3](=O)[NX3][CX3](=O)",
    "aromatic": "a",
}


FUNCTIONAL_GROUP_DOC: dict[str, str] = {
    "epoxy": "环氧基，可与胺、羟基、酸等开环固化。",
    "primary_amine": "伯胺，典型固化剂，可与环氧、酸酐、异氰酸酯反应。",
    "secondary_amine": "仲胺，可参与环氧和异氰酸酯反应。",
    "anhydride": "酸酐，可与胺形成酰亚胺/酰胺酸，也可与羟基形成酯。",
    "isocyanate": "异氰酸酯，可与羟基形成聚氨酯，与胺形成聚脲。",
    "hydroxyl": "醇羟基，可与异氰酸酯、酸酐/羧酸反应。",
    "phenol": "酚羟基，常见于氰酸酯/环氧体系和高 Tg 芳香骨架。",
    "carboxylic_acid": "羧酸，可与环氧/羟基/胺反应。",
    "ester": "酯基，通常作为结构基团而非主要交联反应位点。",
    "ether": "醚键，柔性链段或芳香醚骨架。",
    "acrylate_or_methacrylate": "丙烯酸酯/甲基丙烯酸酯，适合自由基聚合。",
    "vinyl": "乙烯基，可参与自由基、硫醇-烯等反应。",
    "thiol": "硫醇，可与烯基/丙烯酸酯进行 thiol-ene 反应。",
    "cyanate_ester": "氰酸酯，可三聚成高 Tg 三嗪网络，也可与酚/胺共固化。",
    "nitrile": "腈基，通常作为极性结构基团。",
    "maleimide": "马来酰亚胺，可与胺/硫醇/双烯反应。",
    "imide": "酰亚胺，高 Tg/高热稳定结构基团。",
    "aromatic": "芳香结构，通常提高刚性、Tg 和热稳定性。",
}


COMPATIBLE_GROUPS: dict[tuple[str, str], str] = {
    ("epoxy", "primary_amine"): "环氧-伯胺开环固化。",
    ("epoxy", "secondary_amine"): "环氧-仲胺开环固化。",
    ("epoxy", "anhydride"): "环氧-酸酐固化，常需催化剂。",
    ("epoxy", "carboxylic_acid"): "环氧-羧酸开环酯化。",
    ("epoxy", "hydroxyl"): "环氧-羟基醚化，常需催化剂。",
    ("anhydride", "primary_amine"): "酸酐-胺形成聚酰胺酸/聚酰亚胺前体。",
    ("anhydride", "secondary_amine"): "酸酐-胺开环形成酰胺酸。",
    ("anhydride", "hydroxyl"): "酸酐-羟基酯化。",
    ("anhydride", "phenol"): "酸酐-酚羟基酯化。",
    ("isocyanate", "hydroxyl"): "异氰酸酯-羟基形成聚氨酯。",
    ("isocyanate", "phenol"): "异氰酸酯-酚羟基形成氨基甲酸酯。",
    ("isocyanate", "primary_amine"): "异氰酸酯-伯胺形成聚脲。",
    ("isocyanate", "secondary_amine"): "异氰酸酯-仲胺形成脲键。",
    ("thiol", "vinyl"): "硫醇-烯点击反应。",
    ("thiol", "acrylate_or_methacrylate"): "硫醇-Michael/thiol-ene 反应。",
    ("acrylate_or_methacrylate", "vinyl"): "自由基共聚。",
    ("acrylate_or_methacrylate", "acrylate_or_methacrylate"): "自由基均/共聚形成交联网络。",
    ("cyanate_ester", "cyanate_ester"): "氰酸酯三聚形成三嗪网络。",
    ("cyanate_ester", "phenol"): "氰酸酯-酚共固化/催化三聚。",
    ("cyanate_ester", "primary_amine"): "氰酸酯-胺共反应。",
    ("maleimide", "primary_amine"): "马来酰亚胺-胺 Michael 加成。",
    ("maleimide", "thiol"): "马来酰亚胺-硫醇 Michael 加成。",
    ("maleimide", "vinyl"): "马来酰亚胺与烯基共聚/加成。",
}


@dataclass(frozen=True)
class FunctionalGroupResult:
    smiles: str
    groups: tuple[str, ...]
    invalid: bool = False


def classify_smiles(smiles: str) -> FunctionalGroupResult:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return FunctionalGroupResult(smiles=smiles, groups=(), invalid=True)
    groups = []
    for name, smarts in SMARTS.items():
        patt = Chem.MolFromSmarts(smarts)
        if patt is not None and mol.HasSubstructMatch(patt):
            groups.append(name)
    return FunctionalGroupResult(smiles=smiles, groups=tuple(sorted(set(groups))))


def compatibility_reason(groups_a: Iterable[str], groups_b: Iterable[str]) -> str | None:
    for ga in groups_a:
        for gb in groups_b:
            if (ga, gb) in COMPATIBLE_GROUPS:
                return COMPATIBLE_GROUPS[(ga, gb)]
            if (gb, ga) in COMPATIBLE_GROUPS:
                return COMPATIBLE_GROUPS[(gb, ga)]
    return None


def is_reasonable_pair(smiles_a: str, smiles_b: str) -> tuple[bool, str]:
    a = classify_smiles(smiles_a)
    b = classify_smiles(smiles_b)
    if a.invalid or b.invalid:
        return False, "invalid SMILES"
    reason = compatibility_reason(a.groups, b.groups)
    if reason:
        return True, reason
    return False, "no mapped reactive functional-group pair"


def classify_many(smiles: Iterable[str]) -> list[dict[str, str]]:
    rows = []
    for smi in smiles:
        result = classify_smiles(smi)
        rows.append(
            {
                "smiles": smi,
                "groups": ";".join(result.groups),
                "invalid": str(result.invalid),
            }
        )
    return rows

