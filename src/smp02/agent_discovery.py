from __future__ import annotations

import argparse
import hashlib
import itertools
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import torch
from rdkit import Chem, DataStructs
from rdkit.Chem import Descriptors, rdFingerprintGenerator, rdMolDescriptors
from tqdm.auto import tqdm

from smp02.data import canonicalize_smiles, iter_chembl_smiles, load_smp_records, unique_monomers
from smp02.functional_groups import COMPATIBLE_GROUPS, SMARTS, compatibility_reason
from smp02.predictors import load_predictor
from smp02.utils import ensure_dir, load_config, resolve_device, save_json, set_seed
from smp02.vae import encode_smiles, load_vae_checkpoint


ALLOWED_ATOMS = {"B", "Br", "C", "Cl", "F", "H", "I", "N", "O", "P", "S", "Si"}
REACTIVE_GROUPS = {
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


GENERATED_MONOMER_SEEDS: list[tuple[str, str]] = [
    ("generated_diamine_dds", "Nc1ccc(S(=O)(=O)c2ccc(N)cc2)cc1"),
    ("generated_diamine_oda", "Nc1ccc(Oc2ccc(N)cc2)cc1"),
    ("generated_diamine_mda", "Nc1ccc(Cc2ccc(N)cc2)cc1"),
    ("generated_diamine_benzidine", "Nc1ccc(-c2ccc(N)cc2)cc1"),
    ("generated_diamine_mpda", "Nc1cccc(N)c1"),
    ("generated_diamine_ppda", "Nc1ccc(N)cc1"),
    ("generated_diamine_bisphenol_a_core", "Nc1ccc(C(C)(C)c2ccc(N)cc2)cc1"),
    ("generated_diamine_fluorinated_core", "Nc1ccc(C(C(F)(F)F)(C(F)(F)F)c2ccc(N)cc2)cc1"),
    ("generated_dianhydride_bpda", "O=C1OC(=O)c2ccc(-c3ccc4c(c3)C(=O)OC4=O)cc21"),
    ("generated_dianhydride_odpa", "O=C1OC(=O)c2ccc(Oc3ccc4c(c3)C(=O)OC4=O)cc21"),
    ("generated_dianhydride_btda", "O=C1OC(=O)c2ccc(C(=O)c3ccc4c(c3)C(=O)OC4=O)cc21"),
    ("generated_dianhydride_6fda", "O=C1OC(=O)c2cc(C(c3ccc4c(c3)C(=O)OC4=O)(C(F)(F)F)C(F)(F)F)ccc21"),
    ("generated_diepoxy_bpa", "CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1"),
    ("generated_diepoxy_bpf", "c1ccc(C(c2ccc(OCC3CO3)cc2)c2ccc(OCC3CO3)cc2)cc1"),
    ("generated_dicyanate_bpa", "N#COc1ccc(C(C)(C)c2ccc(OC#N)cc2)cc1"),
    ("generated_dicyanate_biphenyl", "N#COc1ccc(-c2ccc(OC#N)cc2)cc1"),
    ("generated_bismaleimide_mda", "O=C1C=CC(=O)N1c1ccc(Cc2ccc(N3C(=O)C=CC3=O)cc2)cc1"),
    ("generated_bismaleimide_oda", "O=C1C=CC(=O)N1c1ccc(Oc2ccc(N3C(=O)C=CC3=O)cc2)cc1"),
    ("generated_bisphenol_s", "Oc1ccc(S(=O)(=O)c2ccc(O)cc2)cc1"),
    ("generated_bisphenol_a", "Oc1ccc(C(C)(C)c2ccc(O)cc2)cc1"),
    ("generated_diisocyanate_ppdi", "O=C=Nc1ccc(N=C=O)cc1"),
    ("generated_diisocyanate_mdi", "O=C=Nc1ccc(Cc2ccc(N=C=O)cc2)cc1"),
    ("generated_dithiol_xylylene", "SCc1ccc(CS)cc1"),
]


@dataclass
class AgentConfig:
    target_tg_c: float
    target_window_c: float
    output_dir: Path
    latent_size: int
    vae_checkpoint: Path
    predictor_path: Path
    training_features_path: Path
    max_components: int
    min_components: int
    min_ratio: float
    require_out_of_library: bool
    generated_pool_limit: int
    chembl_limit: int
    chembl_pool_limit: int
    library_pool_limit: int
    pair_pool_limit: int
    iterations: int
    samples_per_iteration: int
    elite_k: int
    selected_top_k: int
    prediction_batch_size: int
    encode_batch_size: int
    prior_learning_rate: float
    uncertainty_weight: float
    ood_weight: float
    prior_weight: float
    novelty_weight: float
    component_count_weight: float


@dataclass
class Principle:
    name: str
    kind: str
    description: str
    feature: str
    effect: float
    weight: float
    confidence: float
    frozen: bool = False
    evidence_count: int = 0


@dataclass
class MonomerCandidate:
    smiles: str
    source: str
    label: str
    groups: tuple[str, ...]
    monomer_prior_score: float
    molecular_weight: float
    heavy_atoms: int
    aromatic_rings: int
    rotatable_bonds: int
    functionality: int
    in_library: bool
    features: dict[str, bool]


@dataclass
class FormulaCandidate:
    smiles: tuple[str, ...]
    ratios: tuple[float, ...]
    sources: tuple[str, ...]
    labels: tuple[str, ...]
    groups: tuple[str, ...]
    compatibility_reasons: tuple[str, ...]
    features: dict[str, bool]
    prior_score: float
    new_component_count: int


def parse_agent_config(cfg: dict) -> AgentConfig:
    raw = cfg["agent_discovery"]
    return AgentConfig(
        target_tg_c=float(raw["target_tg_c"]),
        target_window_c=float(raw["target_window_c"]),
        output_dir=Path(raw["output_dir"]),
        latent_size=int(raw["latent_size"]),
        vae_checkpoint=Path(raw["vae_checkpoint"]),
        predictor_path=Path(raw["predictor_path"]),
        training_features_path=Path(raw["training_features_path"]),
        max_components=int(raw["max_components"]),
        min_components=int(raw["min_components"]),
        min_ratio=float(raw["min_ratio"]),
        require_out_of_library=bool(raw["require_out_of_library"]),
        generated_pool_limit=int(raw["generated_pool_limit"]),
        chembl_limit=int(raw["chembl_limit"]),
        chembl_pool_limit=int(raw["chembl_pool_limit"]),
        library_pool_limit=int(raw["library_pool_limit"]),
        pair_pool_limit=int(raw["pair_pool_limit"]),
        iterations=int(raw["iterations"]),
        samples_per_iteration=int(raw["samples_per_iteration"]),
        elite_k=int(raw["elite_k"]),
        selected_top_k=int(raw["selected_top_k"]),
        prediction_batch_size=int(raw["prediction_batch_size"]),
        encode_batch_size=int(raw["encode_batch_size"]),
        prior_learning_rate=float(raw["prior_learning_rate"]),
        uncertainty_weight=float(raw["uncertainty_weight"]),
        ood_weight=float(raw["ood_weight"]),
        prior_weight=float(raw["prior_weight"]),
        novelty_weight=float(raw["novelty_weight"]),
        component_count_weight=float(raw["component_count_weight"]),
    )


def compiled_smarts() -> dict[str, Chem.Mol]:
    return {name: Chem.MolFromSmarts(smarts) for name, smarts in SMARTS.items() if Chem.MolFromSmarts(smarts) is not None}


PATTERNS = compiled_smarts()
SULFONE = Chem.MolFromSmarts("S(=O)(=O)")
LONG_ALIPHATIC = Chem.MolFromSmarts("[CX4]-[CX4]-[CX4]-[CX4]-[CX4]-[CX4]")
PEG_LIKE = Chem.MolFromSmarts("[OX2][CX4][CX4][OX2][CX4][CX4][OX2]")
AMIDE = Chem.MolFromSmarts("[CX3](=O)[NX3]")


def classify_mol(mol: Chem.Mol) -> tuple[tuple[str, ...], dict[str, int]]:
    counts: dict[str, int] = {}
    for name, pattern in PATTERNS.items():
        matches = mol.GetSubstructMatches(pattern)
        if matches:
            counts[name] = len(matches)
    return tuple(sorted(counts)), counts


def allowed_atom_set(mol: Chem.Mol) -> bool:
    return all(atom.GetSymbol() in ALLOWED_ATOMS for atom in mol.GetAtoms())


def one_fragment(mol: Chem.Mol) -> bool:
    return len(Chem.GetMolFrags(mol)) == 1


def encodable(smiles: str, charset: list[str], max_length: int) -> bool:
    allowed = set(charset)
    return len(smiles) <= max_length and all(ch in allowed for ch in smiles)


def functionality_estimate(counts: dict[str, int]) -> int:
    return int(sum(counts.get(group, 0) for group in REACTIVE_GROUPS))


def monomer_features(mol: Chem.Mol, groups: tuple[str, ...], counts: dict[str, int]) -> dict[str, bool]:
    aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
    rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
    mw = Descriptors.MolWt(mol)
    has_sulfone = bool(SULFONE is not None and mol.HasSubstructMatch(SULFONE))
    has_long_aliphatic = bool(LONG_ALIPHATIC is not None and mol.HasSubstructMatch(LONG_ALIPHATIC))
    has_peg_like = bool(PEG_LIKE is not None and mol.HasSubstructMatch(PEG_LIKE))
    amide_count = len(mol.GetSubstructMatches(AMIDE)) if AMIDE is not None else 0
    fluorine_count = sum(1 for atom in mol.GetAtoms() if atom.GetSymbol() == "F")
    heavy_halogen_count = sum(1 for atom in mol.GetAtoms() if atom.GetSymbol() in {"Br", "I"})
    chiral_centers = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))
    hba = rdMolDescriptors.CalcNumHBA(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    formal_charge = sum(atom.GetFormalCharge() for atom in mol.GetAtoms())
    group_set = set(groups)
    return {
        "aromatic_backbone": aromatic_rings >= 1,
        "rigid_multi_aromatic": aromatic_rings >= 2,
        "imide_or_anhydride": "imide" in group_set or "anhydride" in group_set,
        "cyanate_ester": "cyanate_ester" in group_set,
        "maleimide": "maleimide" in group_set,
        "nitrile_rich": counts.get("nitrile", 0) >= 2,
        "sulfone_linker": has_sulfone,
        "fluorinated_rigid_linker": fluorine_count >= 3 and aromatic_rings >= 1,
        "high_functionality": functionality_estimate(counts) >= 2,
        "flexible_ether_risk": counts.get("ether", 0) >= 3 and aromatic_rings <= 1,
        "long_aliphatic_risk": has_long_aliphatic,
        "peg_like_risk": has_peg_like,
        "peptide_like_risk": amide_count >= 5,
        "too_flexible_risk": rotatable >= 14,
        "too_large_risk": mw > 700,
        "heavy_halogen_risk": heavy_halogen_count >= 1,
        "stereochemical_complexity_risk": chiral_centers >= 2,
        "druglike_hetero_complexity_risk": (hba + hbd) >= 10 and functionality_estimate(counts) <= 2,
        "formal_charge_practical_risk": formal_charge != 0,
    }


def monomer_prior_score(features: dict[str, bool]) -> float:
    positive = {
        "aromatic_backbone": 0.45,
        "rigid_multi_aromatic": 0.65,
        "imide_or_anhydride": 0.85,
        "cyanate_ester": 0.95,
        "maleimide": 0.8,
        "nitrile_rich": 0.55,
        "sulfone_linker": 0.55,
        "fluorinated_rigid_linker": 0.35,
        "high_functionality": 0.6,
    }
    negative = {
        "flexible_ether_risk": 0.45,
        "long_aliphatic_risk": 0.4,
        "peg_like_risk": 0.75,
        "peptide_like_risk": 1.1,
        "too_flexible_risk": 0.7,
        "too_large_risk": 0.55,
        "heavy_halogen_risk": 0.45,
        "stereochemical_complexity_risk": 0.45,
        "druglike_hetero_complexity_risk": 0.65,
        "formal_charge_practical_risk": 0.55,
    }
    return sum(weight for name, weight in positive.items() if features.get(name)) - sum(
        weight for name, weight in negative.items() if features.get(name)
    )


def initial_principles() -> list[Principle]:
    principles = [
        Principle("aromatic_backbones_raise_tg", "soft", "Aromatic backbones tend to raise Tg.", "aromatic_backbone", 1.0, 0.55, 0.70),
        Principle("multi_aromatic_rigidity", "soft", "Multiple aromatic rings increase chain rigidity.", "rigid_multi_aromatic", 1.0, 0.65, 0.65),
        Principle(
            "imide_anhydride_networks_raise_tg",
            "soft",
            "Imide or anhydride-derived networks often provide high Tg.",
            "imide_or_anhydride",
            1.0,
            0.85,
            0.70,
        ),
        Principle("cyanate_ester_triazine", "soft", "Cyanate ester triazine networks can be high Tg.", "cyanate_ester", 1.0, 0.9, 0.60),
        Principle("maleimide_rigid_network", "soft", "Bismaleimide motifs can create rigid high-Tg networks.", "maleimide", 1.0, 0.75, 0.58),
        Principle("nitrile_rich_rigidity", "soft", "Nitrile-rich aromatic monomers often stiffen networks.", "nitrile_rich", 1.0, 0.45, 0.55),
        Principle("sulfone_diamine_rigidity", "soft", "Sulfone-linked aromatic diamines are common high-Tg hard segments.", "sulfone_linker", 1.0, 0.55, 0.55),
        Principle(
            "high_functionality_crosslink_density",
            "soft",
            "Higher reactive functionality can increase crosslink density.",
            "high_functionality",
            1.0,
            0.55,
            0.62,
        ),
        Principle("flexible_ether_penalty", "soft", "Long flexible ether segments can lower Tg.", "flexible_ether_risk", -1.0, 0.55, 0.68),
        Principle("peg_like_penalty", "soft", "PEG-like segments are a strong low-Tg risk.", "peg_like_risk", -1.0, 0.75, 0.70),
        Principle("long_aliphatic_penalty", "soft", "Long aliphatic segments usually lower Tg.", "long_aliphatic_risk", -1.0, 0.45, 0.62),
        Principle("peptide_like_out_of_domain", "soft", "Peptide-like ChEMBL molecules are poor monomer hypotheses.", "peptide_like_risk", -1.0, 0.75, 0.80),
        Principle("too_flexible_penalty", "soft", "High rotatable-bond count increases flexibility risk.", "too_flexible_risk", -1.0, 0.45, 0.62),
        Principle("heavy_halogen_practical_risk", "soft", "Iodinated or brominated drug-like structures are lower-priority monomer hypotheses.", "heavy_halogen_risk", -1.0, 0.40, 0.62),
        Principle("stereochemical_complexity_penalty", "soft", "Many stereocenters often indicate bioactive-molecule complexity rather than monomer suitability.", "stereochemical_complexity_risk", -1.0, 0.40, 0.62),
        Principle("druglike_hetero_complexity_penalty", "soft", "High HBA/HBD complexity is a risk for out-of-library monomer transfer.", "druglike_hetero_complexity_risk", -1.0, 0.50, 0.62),
        Principle("formal_charge_practical_penalty", "soft", "Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified.", "formal_charge_practical_risk", -1.0, 0.45, 0.62),
    ]
    for (a, b), reason in COMPATIBLE_GROUPS.items():
        feature = f"reaction::{reason}"
        name = "reaction_" + safe_slug(reason)
        principles.append(
            Principle(
                name=name,
                kind="soft",
                description=f"Reaction principle: {reason}",
                feature=feature,
                effect=1.0,
                weight=0.42,
                confidence=0.55,
            )
        )
    return principles


def safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text.encode("ascii", "ignore").decode("ascii")).strip("_").lower()
    if slug:
        return slug[:60]
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def add_monomer(
    pool: dict[str, MonomerCandidate],
    smiles: str,
    source: str,
    label: str,
    library_set: set[str],
    charset: list[str],
    max_length: int,
) -> None:
    canonical = canonicalize_smiles(smiles)
    if canonical is None or canonical in pool:
        return
    if canonical.count(".") > 0 or not encodable(canonical, charset, max_length):
        return
    mol = Chem.MolFromSmiles(canonical)
    if mol is None or not one_fragment(mol) or not allowed_atom_set(mol):
        return
    groups, counts = classify_mol(mol)
    if not set(groups) & REACTIVE_GROUPS:
        return
    heavy_atoms = int(mol.GetNumHeavyAtoms())
    mw = float(Descriptors.MolWt(mol))
    if heavy_atoms < 5 or heavy_atoms > 80 or mw < 70 or mw > 850:
        return
    features = monomer_features(mol, groups, counts)
    if features.get("peptide_like_risk") or features.get("too_large_risk"):
        return
    actual_source = "library" if canonical in library_set else source
    pool[canonical] = MonomerCandidate(
        smiles=canonical,
        source=actual_source,
        label=label,
        groups=groups,
        monomer_prior_score=monomer_prior_score(features),
        molecular_weight=mw,
        heavy_atoms=heavy_atoms,
        aromatic_rings=int(rdMolDescriptors.CalcNumAromaticRings(mol)),
        rotatable_bonds=int(rdMolDescriptors.CalcNumRotatableBonds(mol)),
        functionality=functionality_estimate(counts),
        in_library=canonical in library_set,
        features=features,
    )


def build_monomer_pool(cfg: dict, agent_cfg: AgentConfig, charset: list[str], max_length: int) -> tuple[list[MonomerCandidate], list[str]]:
    records = load_smp_records(cfg["data_path"])
    library_monomers = unique_monomers(records)
    library_set = set(library_monomers)
    pool: dict[str, MonomerCandidate] = {}
    for idx, smiles in enumerate(library_monomers):
        add_monomer(pool, smiles, "library", f"library_{idx}", library_set, charset, max_length)

    for label, smiles in GENERATED_MONOMER_SEEDS[: agent_cfg.generated_pool_limit]:
        add_monomer(pool, smiles, "generated", label, library_set, charset, max_length)

    chembl_added = 0
    chembl_seen = 0
    chembl_iter = iter_chembl_smiles(cfg["chembl_path"], limit=agent_cfg.chembl_limit, max_length=max_length, validate=False)
    for chembl_seen, smiles in enumerate(tqdm(chembl_iter, desc="scan chembl for out-of-library monomers", leave=False), start=1):
        before = len(pool)
        add_monomer(pool, smiles, "chembl", f"chembl_scan_{chembl_seen}", library_set, charset, max_length)
        if len(pool) > before and next(reversed(pool.values())).source == "chembl":
            chembl_added += 1
        if chembl_added >= agent_cfg.chembl_pool_limit * 8:
            break

    monomers = list(pool.values())
    library = [m for m in monomers if m.source == "library"]
    generated = [m for m in monomers if m.source == "generated"]
    chembl = [m for m in monomers if m.source == "chembl"]
    library = sorted(library, key=lambda m: m.monomer_prior_score, reverse=True)[: agent_cfg.library_pool_limit]
    generated = sorted(generated, key=lambda m: m.monomer_prior_score, reverse=True)[: agent_cfg.generated_pool_limit]
    chembl = diverse_by_group(sorted(chembl, key=lambda m: m.monomer_prior_score, reverse=True), agent_cfg.chembl_pool_limit)
    selected = library + generated + chembl
    selected = sorted({m.smiles: m for m in selected}.values(), key=lambda m: (m.source != "library", -m.monomer_prior_score, m.smiles))
    stats = [
        f"library={sum(m.source == 'library' for m in selected)}",
        f"generated={sum(m.source == 'generated' for m in selected)}",
        f"chembl={sum(m.source == 'chembl' for m in selected)}",
        f"chembl_scanned={chembl_seen}",
    ]
    return selected, stats


def diverse_by_group(monomers: list[MonomerCandidate], limit: int) -> list[MonomerCandidate]:
    selected: list[MonomerCandidate] = []
    per_signature: dict[str, int] = {}
    for monomer in monomers:
        signature = ";".join(sorted(set(monomer.groups) & REACTIVE_GROUPS))
        quota = 40 if signature else 10
        if per_signature.get(signature, 0) >= quota and len(selected) < limit // 2:
            continue
        selected.append(monomer)
        per_signature[signature] = per_signature.get(signature, 0) + 1
        if len(selected) >= limit:
            break
    return selected


def compatibility_edges(monomers: list[MonomerCandidate]) -> tuple[list[str], list[tuple[int, int, str]]]:
    participating = [False] * len(monomers)
    reasons: list[str] = []
    edges: list[tuple[int, int, str]] = []
    for i, j in itertools.combinations(range(len(monomers)), 2):
        reason = compatibility_reason(monomers[i].groups, monomers[j].groups)
        if reason:
            participating[i] = True
            participating[j] = True
            reasons.append(reason)
            edges.append((i, j, reason))
    return sorted(set(reasons)), edges


def formulation_valid(monomers: list[MonomerCandidate], ratios: tuple[float, ...], min_ratio: float) -> tuple[bool, tuple[str, ...]]:
    if any(r < min_ratio - 1e-9 for r in ratios) or abs(sum(ratios) - 1.0) > 1e-6:
        return False, ()
    if len(monomers) == 1:
        reason = compatibility_reason(monomers[0].groups, monomers[0].groups)
        if reason and monomers[0].functionality >= 2:
            return True, (reason,)
        return False, ()
    reasons, edges = compatibility_edges(monomers)
    if not edges:
        return False, ()
    participating = [False] * len(monomers)
    for i, j, _ in edges:
        participating[i] = True
        participating[j] = True
    for idx, ok in enumerate(participating):
        if not ok and ratios[idx] > 0.10:
            return False, tuple(reasons)
    return True, tuple(reasons)


def normalize_ratios(values: np.ndarray) -> tuple[float, ...]:
    values = np.maximum(values.astype(float), 0.0)
    total = float(values.sum())
    if total <= 0:
        return tuple()
    ratios = values / total
    rounded = np.round(ratios, 5)
    correction = 1.0 - float(rounded.sum())
    rounded[-1] += correction
    return tuple(float(x) for x in rounded)


def formula_key(smiles: tuple[str, ...], ratios: tuple[float, ...]) -> str:
    return "|".join(f"{s}@{r:.4f}" for s, r in zip(smiles, ratios, strict=False))


def formula_features(
    monomers: list[MonomerCandidate],
    reasons: tuple[str, ...],
    new_component_count: int,
) -> dict[str, bool]:
    features: dict[str, bool] = {}
    for monomer in monomers:
        for name, value in monomer.features.items():
            features[name] = features.get(name, False) or bool(value)
    for reason in reasons:
        features[f"reaction::{reason}"] = True
    features["contains_out_of_library"] = new_component_count > 0
    features["contains_generated"] = any(m.source == "generated" for m in monomers)
    features["contains_chembl"] = any(m.source == "chembl" for m in monomers)
    features["three_or_more_component_blending"] = len(monomers) >= 3
    return features


def compute_prior_score(features: dict[str, bool], principles: list[Principle]) -> float:
    score = 0.0
    for principle in principles:
        if features.get(principle.feature, False):
            score += principle.effect * principle.weight * principle.confidence
    return float(score)


def build_formula(
    monomers: list[MonomerCandidate],
    ratios: tuple[float, ...],
    principles: list[Principle],
    min_ratio: float,
) -> FormulaCandidate | None:
    ordered = sorted(zip(monomers, ratios, strict=False), key=lambda item: item[0].smiles)
    monomers = [item[0] for item in ordered]
    ratios = normalize_ratios(np.asarray([item[1] for item in ordered], dtype=float))
    ok, reasons = formulation_valid(monomers, ratios, min_ratio)
    if not ok:
        return None
    new_count = sum(not m.in_library for m in monomers)
    features = formula_features(monomers, reasons, new_count)
    return FormulaCandidate(
        smiles=tuple(m.smiles for m in monomers),
        ratios=ratios,
        sources=tuple(m.source for m in monomers),
        labels=tuple(m.label for m in monomers),
        groups=tuple(";".join(m.groups) for m in monomers),
        compatibility_reasons=reasons,
        features=features,
        prior_score=compute_prior_score(features, principles),
        new_component_count=new_count,
    )


def systematic_pair_formulas(
    pool: list[MonomerCandidate],
    principles: list[Principle],
    min_ratio: float,
    require_out: bool,
    limit: int,
) -> list[FormulaCandidate]:
    selected_pool = sorted(pool, key=lambda m: m.monomer_prior_score, reverse=True)[:limit]
    formulas: list[FormulaCandidate] = []
    seen: set[str] = set()
    ratios = [round(x, 2) for x in np.arange(min_ratio, 1.0 - min_ratio + 1e-9, 0.10)]
    for i, j in itertools.combinations(range(len(selected_pool)), 2):
        a = selected_pool[i]
        b = selected_pool[j]
        if require_out and a.in_library and b.in_library:
            continue
        if compatibility_reason(a.groups, b.groups) is None:
            continue
        for ratio_a in ratios:
            formula = build_formula([a, b], (ratio_a, 1.0 - ratio_a), principles, min_ratio)
            if formula is None:
                continue
            key = formula_key(formula.smiles, formula.ratios)
            if key not in seen:
                seen.add(key)
                formulas.append(formula)
    return formulas


def random_formulas(
    pool: list[MonomerCandidate],
    principles: list[Principle],
    rng: np.random.Generator,
    count: int,
    min_components: int,
    max_components: int,
    min_ratio: float,
    require_out: bool,
    seen: set[str],
) -> list[FormulaCandidate]:
    formulas: list[FormulaCandidate] = []
    weights = np.asarray([max(0.05, m.monomer_prior_score + 2.5) for m in pool], dtype=float)
    weights = weights / weights.sum()
    new_indices = np.asarray([idx for idx, monomer in enumerate(pool) if not monomer.in_library], dtype=int)
    component_values = np.arange(min_components, max_components + 1)
    component_probs = np.asarray([0.08, 0.42, 0.35, 0.15][: len(component_values)], dtype=float)
    component_probs = component_probs / component_probs.sum()
    attempts = 0
    max_attempts = max(count * 80, 5000)
    while len(formulas) < count and attempts < max_attempts:
        attempts += 1
        n = int(rng.choice(component_values, p=component_probs))
        if require_out and len(new_indices) > 0:
            chosen = [int(rng.choice(new_indices))]
            while len(chosen) < n:
                idx = int(rng.choice(len(pool), p=weights))
                if idx not in chosen:
                    chosen.append(idx)
        else:
            chosen = []
            while len(chosen) < n:
                idx = int(rng.choice(len(pool), p=weights))
                if idx not in chosen:
                    chosen.append(idx)
        monomers = [pool[idx] for idx in chosen]
        if n == 1:
            ratios = (1.0,)
        else:
            raw = rng.dirichlet(np.full(n, 1.35))
            if raw.min() < min_ratio:
                continue
            ratios = normalize_ratios(raw)
        formula = build_formula(monomers, ratios, principles, min_ratio)
        if formula is None:
            continue
        if require_out and formula.new_component_count == 0:
            continue
        key = formula_key(formula.smiles, formula.ratios)
        if key in seen:
            continue
        seen.add(key)
        formulas.append(formula)
    return formulas


def formulas_to_features(formulas: list[FormulaCandidate], vectors: dict[str, np.ndarray], latent_size: int) -> np.ndarray:
    x = np.zeros((len(formulas), latent_size), dtype=np.float32)
    for row, formula in enumerate(formulas):
        for smiles, ratio in zip(formula.smiles, formula.ratios, strict=False):
            x[row] += float(ratio) * vectors[smiles].astype(np.float32)
    return x


def predict_with_uncertainty(bundle: dict, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x_scaled = bundle["x_scaler"].transform(x)
    model = bundle["model"]
    if hasattr(model, "predict"):
        try:
            y_scaled, std_scaled = model.predict(x_scaled, return_std=True)
            mean = bundle["y_scaler"].inverse_transform(np.asarray(y_scaled).reshape(-1, 1)).ravel()
            data_range = float(getattr(bundle["y_scaler"], "data_range_", np.asarray([1.0]))[0])
            std = np.asarray(std_scaled, dtype=float).reshape(-1) * data_range
            return mean, std
        except TypeError:
            pass
    y_scaled = model.predict(x_scaled)
    mean = bundle["y_scaler"].inverse_transform(np.asarray(y_scaled).reshape(-1, 1)).ravel()
    return mean, np.full(len(mean), np.nan)


def nearest_distances(x: np.ndarray, reference: np.ndarray, batch_size: int = 8192) -> np.ndarray:
    ref = reference.astype(np.float32)
    ref_norm = np.sum(ref * ref, axis=1)
    mins: list[np.ndarray] = []
    for start in range(0, len(x), batch_size):
        chunk = x[start : start + batch_size].astype(np.float32)
        dist2 = np.sum(chunk * chunk, axis=1, keepdims=True) + ref_norm.reshape(1, -1) - 2.0 * chunk @ ref.T
        mins.append(np.sqrt(np.maximum(dist2.min(axis=1), 0.0)))
    return np.concatenate(mins) if mins else np.empty(0, dtype=float)


def ood_reference_scale(reference: np.ndarray) -> float:
    if len(reference) < 3:
        return 1.0
    ref = reference.astype(np.float32)
    ref_norm = np.sum(ref * ref, axis=1)
    dist2 = ref_norm.reshape(-1, 1) + ref_norm.reshape(1, -1) - 2.0 * ref @ ref.T
    np.fill_diagonal(dist2, np.inf)
    nearest = np.sqrt(np.maximum(dist2.min(axis=1), 0.0))
    nearest = nearest[np.isfinite(nearest) & (nearest > 1e-8)]
    if len(nearest) == 0:
        return 1.0
    return float(np.median(nearest))


def evaluate_formulas(
    formulas: list[FormulaCandidate],
    vectors: dict[str, np.ndarray],
    predictor: dict,
    train_features: np.ndarray,
    ood_scale: float,
    agent_cfg: AgentConfig,
) -> pd.DataFrame:
    if not formulas:
        return pd.DataFrame()
    x = formulas_to_features(formulas, vectors, agent_cfg.latent_size)
    means: list[np.ndarray] = []
    stds: list[np.ndarray] = []
    for start in range(0, len(x), agent_cfg.prediction_batch_size):
        mean, std = predict_with_uncertainty(predictor, x[start : start + agent_cfg.prediction_batch_size])
        means.append(mean)
        stds.append(std)
    pred = np.concatenate(means)
    sigma = np.concatenate(stds)
    ood = nearest_distances(x, train_features, agent_cfg.prediction_batch_size)
    ood_penalty = ood / max(ood_scale, 1e-8)
    rows = []
    for idx, formula in enumerate(formulas):
        target_distance = abs(float(pred[idx]) - agent_cfg.target_tg_c)
        sigma_value = float(sigma[idx]) if np.isfinite(sigma[idx]) else 0.0
        n_components = len(formula.smiles)
        score = (
            target_distance
            + agent_cfg.uncertainty_weight * sigma_value
            + agent_cfg.ood_weight * float(ood_penalty[idx])
            + agent_cfg.component_count_weight * max(0, n_components - 2)
            - agent_cfg.prior_weight * formula.prior_score
            - agent_cfg.novelty_weight * min(formula.new_component_count, 2)
        )
        rows.append(
            {
                "formula_id": idx,
                "n_components": n_components,
                "smiles": "|".join(formula.smiles),
                "ratios": ":".join(f"{r:.5f}" for r in formula.ratios),
                "sources": "|".join(formula.sources),
                "labels": "|".join(formula.labels),
                "groups": "|".join(formula.groups),
                "new_component_count": formula.new_component_count,
                "compatibility_reasons": "|".join(formula.compatibility_reasons),
                "predicted_tg_mean_c": float(pred[idx]),
                "predicted_tg_sigma_c": float(sigma[idx]) if np.isfinite(sigma[idx]) else np.nan,
                "target_distance_c": target_distance,
                "prior_score": formula.prior_score,
                "ood_distance": float(ood[idx]),
                "ood_penalty": float(ood_penalty[idx]),
                "agent_score": float(score),
                **{f"feature_{name}": value for name, value in formula.features.items()},
            }
        )
    return pd.DataFrame(rows)


def update_principles(principles: list[Principle], scored: pd.DataFrame, agent_cfg: AgentConfig) -> dict[str, object]:
    if scored.empty:
        return {"updated": 0, "anomalies": [], "added_principles": []}
    elite = scored.sort_values(["target_distance_c", "agent_score"]).head(agent_cfg.elite_k).copy()
    reward = np.exp(-elite["target_distance_c"].to_numpy(dtype=float) / max(agent_cfg.target_window_c, 1e-6))
    if "predicted_tg_sigma_c" in elite:
        sigma = elite["predicted_tg_sigma_c"].fillna(0.0).to_numpy(dtype=float)
        reward = reward - 0.002 * sigma
    if "ood_penalty" in elite:
        reward = reward - 0.03 * elite["ood_penalty"].to_numpy(dtype=float)
    global_reward = float(np.mean(reward)) if len(reward) else 0.0
    updated = 0
    for principle in principles:
        if principle.frozen:
            continue
        col = f"feature_{principle.feature}"
        if col not in elite.columns:
            continue
        mask = elite[col].astype("boolean").fillna(False).to_numpy(dtype=bool)
        if mask.sum() < 3:
            continue
        feature_reward = float(np.mean(reward[mask]))
        delta = (feature_reward - global_reward) * principle.effect
        principle.confidence = float(np.clip(principle.confidence + agent_cfg.prior_learning_rate * np.tanh(delta), 0.05, 0.98))
        principle.evidence_count += int(mask.sum())
        updated += 1

    anomalies = detect_anomalies(elite, agent_cfg)
    added = augment_principles(principles, elite, agent_cfg)
    return {"updated": updated, "anomalies": anomalies, "added_principles": added}


def detect_anomalies(elite: pd.DataFrame, agent_cfg: AgentConfig) -> list[dict[str, object]]:
    if elite.empty:
        return []
    near = elite[elite["target_distance_c"] <= agent_cfg.target_window_c].copy()
    if near.empty:
        return []
    low_prior_threshold = float(elite["prior_score"].quantile(0.25))
    high_ood_threshold = float(max(2.5, elite["ood_penalty"].quantile(0.90)))
    anomalies = []
    for _, row in near.iterrows():
        reasons = []
        if float(row["prior_score"]) <= low_prior_threshold:
            reasons.append("low_prior_but_near_target")
        if float(row["ood_penalty"]) >= high_ood_threshold:
            reasons.append("high_ood_but_near_target")
        if reasons:
            anomalies.append(
                {
                    "formula": row["smiles"],
                    "ratios": row["ratios"],
                    "predicted_tg_mean_c": float(row["predicted_tg_mean_c"]),
                    "target_distance_c": float(row["target_distance_c"]),
                    "prior_score": float(row["prior_score"]),
                    "ood_penalty": float(row["ood_penalty"]),
                    "reasons": reasons,
                }
            )
    return anomalies[:20]


def augment_principles(principles: list[Principle], elite: pd.DataFrame, agent_cfg: AgentConfig) -> list[str]:
    added: list[str] = []
    existing = {p.name for p in principles}
    near = elite[elite["target_distance_c"] <= agent_cfg.target_window_c]
    if near.empty:
        return added
    if (near["n_components"] >= 3).sum() >= 5 and "observed_three_or_more_component_blending" not in existing:
        principles.append(
            Principle(
                "observed_three_or_more_component_blending",
                "soft",
                "Observed near-target candidates where n>=3 tunes Tg toward the target.",
                "three_or_more_component_blending",
                1.0,
                0.35,
                0.45,
            )
        )
        added.append("observed_three_or_more_component_blending")
    if near["sources"].str.contains("chembl").sum() >= 5 and "observed_chembl_transferable_monomers" not in existing:
        principles.append(
            Principle(
                "observed_chembl_transferable_monomers",
                "soft",
                "Observed ChEMBL molecules passing hard validators and producing near-target predictions.",
                "contains_chembl",
                1.0,
                0.25,
                0.42,
            )
        )
        added.append("observed_chembl_transferable_monomers")
    if near["sources"].str.contains("generated").sum() >= 5 and "observed_template_generated_monomers" not in existing:
        principles.append(
            Principle(
                "observed_template_generated_monomers",
                "soft",
                "Observed generated template monomers passing validators and producing near-target predictions.",
                "contains_generated",
                1.0,
                0.25,
                0.42,
            )
        )
        added.append("observed_template_generated_monomers")
    return added


def principle_state_frame(principles: list[Principle]) -> pd.DataFrame:
    return pd.DataFrame([asdict(p) for p in principles]).sort_values(["kind", "confidence", "weight"], ascending=[True, False, False])


def monomer_pool_frame(pool: list[MonomerCandidate]) -> pd.DataFrame:
    rows = []
    for monomer in pool:
        rows.append(
            {
                "smiles": monomer.smiles,
                "source": monomer.source,
                "label": monomer.label,
                "groups": ";".join(monomer.groups),
                "monomer_prior_score": monomer.monomer_prior_score,
                "molecular_weight": monomer.molecular_weight,
                "heavy_atoms": monomer.heavy_atoms,
                "aromatic_rings": monomer.aromatic_rings,
                "rotatable_bonds": monomer.rotatable_bonds,
                "functionality": monomer.functionality,
                "in_library": monomer.in_library,
                **{f"feature_{name}": value for name, value in monomer.features.items()},
            }
        )
    return pd.DataFrame(rows)


def encode_pool(
    pool: list[MonomerCandidate],
    checkpoint_path: Path,
    device: torch.device,
    batch_size: int,
) -> tuple[dict[str, np.ndarray], list[str], int]:
    vae, checkpoint = load_vae_checkpoint(checkpoint_path, map_location=device)
    vae.to(device)
    charset = checkpoint["charset"]
    max_length = int(checkpoint["max_length"])
    smiles = [m.smiles for m in pool]
    latent = encode_smiles(vae, smiles, charset, max_length, device, batch_size=batch_size)
    return {smiles[i]: latent[i] for i in range(len(smiles))}, charset, max_length


def load_charset_meta(checkpoint_path: Path, device: torch.device) -> tuple[list[str], int]:
    _, checkpoint = load_vae_checkpoint(checkpoint_path, map_location=device)
    return checkpoint["charset"], int(checkpoint["max_length"])


def fingerprint_diversity(smiles_values: Iterable[str]) -> float:
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps = []
    for smiles in smiles_values:
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            fps.append(gen.GetFingerprint(mol))
    if len(fps) < 2:
        return 0.0
    sims = []
    for i in range(len(fps)):
        for j in range(i + 1, len(fps)):
            sims.append(DataStructs.TanimotoSimilarity(fps[i], fps[j]))
    return float(1.0 - np.mean(sims)) if sims else 0.0


def write_report(
    out: Path,
    agent_cfg: AgentConfig,
    selected: pd.DataFrame,
    history: list[dict[str, object]],
    pool_stats: list[str],
    principles: list[Principle],
    validation_summary: dict[str, int | bool],
) -> None:
    lines = [
        "# 250 C Out-of-Library SMP Formula Agent Report",
        "",
        "## Run Summary",
        "",
        f"- Target Tg: {agent_cfg.target_tg_c:.1f} C.",
        f"- Target window for near-hit counting: +/- {agent_cfg.target_window_c:.1f} C.",
        f"- Components searched: n={agent_cfg.min_components}..{agent_cfg.max_components}.",
        f"- Require at least one out-of-library component: {agent_cfg.require_out_of_library}.",
        f"- Pool stats: {', '.join(pool_stats)}.",
        f"- Iterations: {agent_cfg.iterations}; samples per iteration: {agent_cfg.samples_per_iteration}.",
        f"- Selected hard-constraint validation: {validation_summary.get('all_selected_pass', False)} "
        f"({validation_summary.get('selected_rows', 0)} rows checked).",
        "",
        "## Recommended Candidates",
        "",
        "Ranked by `agent_score`, which balances target distance, GPR uncertainty, OOD distance, soft priors, novelty, and component-count cost. The closest-by-Tg table is saved separately as `closest_formulations.csv`.",
        "",
    ]
    if selected.empty:
        lines.append("No candidates were selected.")
    else:
        lines.extend(
            [
                "| Rank | n | Agent score | Tg mean +/- sigma (C) | Distance (C) | OOD | Sources | Ratios | Compatibility | SMILES |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
            ]
        )
        for rank, (_, row) in enumerate(selected.head(25).iterrows(), start=1):
            sigma = row["predicted_tg_sigma_c"]
            sigma_text = "NA" if pd.isna(sigma) else f"{float(sigma):.2f}"
            lines.append(
                f"| {rank} | {int(row['n_components'])} | {float(row['agent_score']):.2f} | "
                f"{float(row['predicted_tg_mean_c']):.2f} +/- {sigma_text} | "
                f"{float(row['target_distance_c']):.2f} | {float(row['ood_penalty']):.2f} | {row['sources']} | {row['ratios']} | "
                f"{str(row['compatibility_reasons'])[:120]} | `{row['smiles']}` |"
            )
    lines.extend(
        [
            "",
            "## Iteration History",
            "",
            "| Iteration | Generated | Best Tg (C) | Best distance (C) | Near target | Added principles |",
            "| ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for item in history:
        lines.append(
            f"| {item['iteration']} | {item['generated_candidates']} | {item['best_predicted_tg_mean_c']:.2f} | "
            f"{item['best_target_distance_c']:.2f} | {item['near_target_count']} | {', '.join(item['added_principles']) or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Current Top Soft Principles",
            "",
            "| Principle | Confidence | Weight | Effect |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for principle in sorted(principles, key=lambda p: p.confidence * p.weight, reverse=True)[:20]:
        lines.append(f"| {principle.name} | {principle.confidence:.3f} | {principle.weight:.3f} | {principle.effect:.1f} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Hard constraints are deterministic and are not changed by the loop: RDKit validity, VAE encodability, ratio simplex, allowed atoms, and functional-group reaction graph validity.",
            "- Soft priors are PiEvo-style beliefs. Their confidence is updated from in-silico predictor observations, so these are model-guidance beliefs, not experimental truth.",
            "- A real synthesis/DSC result should be added as a stronger observation source and should override purely in-silico principle updates.",
        ]
    )
    (out / "agent_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_formula_frame(df: pd.DataFrame, agent_cfg: AgentConfig) -> dict[str, int | bool]:
    if df.empty:
        return {
            "selected_rows": 0,
            "ratio_sum_ok": 0,
            "has_out_of_library": 0,
            "n_range_ok": 0,
            "compatibility_nonempty": 0,
            "rdkit_valid": 0,
            "all_selected_pass": False,
        }

    def ratio_sum_ok(text: str) -> bool:
        try:
            return abs(sum(float(x) for x in str(text).split(":")) - 1.0) < 1e-4
        except Exception:
            return False

    def rdkit_valid(text: str) -> bool:
        return all(Chem.MolFromSmiles(smiles) is not None for smiles in str(text).split("|"))

    rows = int(len(df))
    result: dict[str, int | bool] = {
        "selected_rows": rows,
        "ratio_sum_ok": int(df["ratios"].map(ratio_sum_ok).sum()),
        "has_out_of_library": int((df["new_component_count"] >= 1).sum()),
        "n_range_ok": int(df["n_components"].between(agent_cfg.min_components, agent_cfg.max_components).sum()),
        "compatibility_nonempty": int(df["compatibility_reasons"].fillna("").astype(str).str.len().gt(0).sum()),
        "rdkit_valid": int(df["smiles"].map(rdkit_valid).sum()),
    }
    result["all_selected_pass"] = all(int(result[key]) == rows for key in result if key != "selected_rows")
    return result


def run_agent_discovery(cfg: dict, device: torch.device) -> pd.DataFrame:
    agent_cfg = parse_agent_config(cfg)
    out = ensure_dir(agent_cfg.output_dir)
    if not agent_cfg.vae_checkpoint.exists():
        raise FileNotFoundError(f"Missing VAE checkpoint: {agent_cfg.vae_checkpoint}")
    if not agent_cfg.predictor_path.exists():
        raise FileNotFoundError(f"Missing predictor: {agent_cfg.predictor_path}")
    if not agent_cfg.training_features_path.exists():
        raise FileNotFoundError(f"Missing training features: {agent_cfg.training_features_path}")

    charset, max_length = load_charset_meta(agent_cfg.vae_checkpoint, device)
    pool, pool_stats = build_monomer_pool(cfg, agent_cfg, charset, max_length)
    monomer_pool_frame(pool).to_csv(out / "monomer_pool.csv", index=False)
    vectors, _, _ = encode_pool(pool, agent_cfg.vae_checkpoint, device, agent_cfg.encode_batch_size)
    predictor = load_predictor(agent_cfg.predictor_path)
    train_npz = np.load(agent_cfg.training_features_path)
    train_features = np.asarray(train_npz["x"], dtype=np.float32)
    ood_scale = ood_reference_scale(train_features)
    principles = initial_principles()
    rng = np.random.default_rng(int(cfg.get("seed", 42)))
    all_scored: list[pd.DataFrame] = []
    history: list[dict[str, object]] = []
    global_seen: set[str] = set()

    systematic = systematic_pair_formulas(
        pool,
        principles,
        agent_cfg.min_ratio,
        agent_cfg.require_out_of_library,
        agent_cfg.pair_pool_limit,
    )
    for formula in systematic:
        global_seen.add(formula_key(formula.smiles, formula.ratios))

    for iteration in range(1, agent_cfg.iterations + 1):
        formulas = []
        if iteration == 1:
            formulas.extend(systematic)
        formulas.extend(
            random_formulas(
                pool,
                principles,
                rng,
                max(0, agent_cfg.samples_per_iteration - len(formulas)),
                agent_cfg.min_components,
                agent_cfg.max_components,
                agent_cfg.min_ratio,
                agent_cfg.require_out_of_library,
                global_seen,
            )
        )
        scored = evaluate_formulas(formulas, vectors, predictor, train_features, ood_scale, agent_cfg)
        if scored.empty:
            history.append(
                {
                    "iteration": iteration,
                    "generated_candidates": 0,
                    "best_predicted_tg_mean_c": math.nan,
                    "best_target_distance_c": math.nan,
                    "near_target_count": 0,
                    "updated_principles": 0,
                    "added_principles": [],
                    "anomalies": [],
                }
            )
            continue
        scored["iteration"] = iteration
        update = update_principles(principles, scored, agent_cfg)
        best = scored.sort_values(["target_distance_c", "agent_score"]).iloc[0]
        near_count = int((scored["target_distance_c"] <= agent_cfg.target_window_c).sum())
        history.append(
            {
                "iteration": iteration,
                "generated_candidates": int(len(scored)),
                "best_predicted_tg_mean_c": float(best["predicted_tg_mean_c"]),
                "best_target_distance_c": float(best["target_distance_c"]),
                "near_target_count": near_count,
                "updated_principles": int(update["updated"]),
                "added_principles": update["added_principles"],
                "anomalies": update["anomalies"],
            }
        )
        all_scored.append(scored)

    candidates = pd.concat(all_scored, ignore_index=True) if all_scored else pd.DataFrame()
    if not candidates.empty:
        candidates = candidates.sort_values(["agent_score", "target_distance_c"]).drop_duplicates(subset=["smiles", "ratios"], keep="first")
        candidates.to_csv(out / "candidate_formulations.csv", index=False)
        selected = candidates.sort_values(["agent_score", "target_distance_c"]).head(agent_cfg.selected_top_k).copy()
        selected.to_csv(out / "selected_formulations.csv", index=False)
        closest = candidates.sort_values(["target_distance_c", "agent_score"]).head(agent_cfg.selected_top_k).copy()
        closest.to_csv(out / "closest_formulations.csv", index=False)
    else:
        candidates.to_csv(out / "candidate_formulations.csv", index=False)
        selected = candidates
        selected.to_csv(out / "selected_formulations.csv", index=False)
        selected.to_csv(out / "closest_formulations.csv", index=False)
    principle_state_frame(principles).to_csv(out / "principle_state.csv", index=False)
    save_json([asdict(p) for p in principles], out / "principle_state.json")
    save_json(history, out / "iteration_history.json")
    validation_summary = validate_formula_frame(selected, agent_cfg)
    save_json(validation_summary, out / "validation_summary.json")
    summary = {
        "target_tg_c": agent_cfg.target_tg_c,
        "target_window_c": agent_cfg.target_window_c,
        "pool_stats": pool_stats,
        "n_pool": len(pool),
        "n_candidates": int(len(candidates)),
        "n_selected": int(len(selected)),
        "best_recommended_target_distance_c": None if selected.empty else float(selected.iloc[0]["target_distance_c"]),
        "best_recommended_predicted_tg_mean_c": None if selected.empty else float(selected.iloc[0]["predicted_tg_mean_c"]),
        "best_recommended_agent_score": None if selected.empty else float(selected.iloc[0]["agent_score"]),
        "closest_target_distance_c": None if candidates.empty else float(candidates.sort_values(["target_distance_c", "agent_score"]).iloc[0]["target_distance_c"]),
        "closest_predicted_tg_mean_c": None if candidates.empty else float(candidates.sort_values(["target_distance_c", "agent_score"]).iloc[0]["predicted_tg_mean_c"]),
        "top25_diversity": None if selected.empty else fingerprint_diversity(selected.head(25)["smiles"].map(lambda value: str(value).split("|")[0])),
        "validation": validation_summary,
    }
    save_json(summary, out / "agent_summary.json")
    write_report(out, agent_cfg, selected, history, pool_stats, principles, validation_summary)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Out-of-library SMP formulation discovery agent")
    parser.add_argument("--config", default="configs/agent_250.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    set_seed(int(cfg.get("seed", 42)))
    device = resolve_device(cfg.get("device", "cuda"))
    selected = run_agent_discovery(cfg, device)
    if selected.empty:
        print("No candidates selected.")
    else:
        best = selected.iloc[0]
        print(
            f"Best candidate: Tg={float(best['predicted_tg_mean_c']):.2f} C, "
            f"distance={float(best['target_distance_c']):.2f} C, n={int(best['n_components'])}, "
            f"sources={best['sources']}"
        )


if __name__ == "__main__":
    main()
