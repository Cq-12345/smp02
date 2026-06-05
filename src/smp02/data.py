from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")


TG_COLUMN_CANDIDATES = (
    "Glass transtion temperature",
    "Glass transition temperature",
    "Tg",
    "tg",
)


@dataclass(frozen=True)
class SMPRecord:
    row_index: int
    author: str
    no: str
    names: str
    smiles: tuple[str, ...]
    ratios: tuple[float, ...]
    tg: float


def canonicalize_smiles(smiles: str) -> str | None:
    smiles = str(smiles).strip().strip("'\"")
    if not smiles or smiles.lower() == "nan":
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol, canonical=True)


def parse_smiles_set(raw: object) -> list[str]:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return []
    text = str(raw).strip()
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    parts = [p.strip().strip("'\"") for p in text.split(",")]
    return [p for p in parts if p]


def parse_ratios(raw: object, expected: int) -> list[float]:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        ratios = [1.0 / expected] * expected
    else:
        tokens = re.split(r"[:;,/|\s]+", str(raw).strip())
        ratios = [float(t) for t in tokens if t]
    if len(ratios) != expected:
        raise ValueError(f"ratio count {len(ratios)} does not match smiles count {expected}")
    total = float(sum(ratios))
    if total <= 0:
        raise ValueError("ratio sum must be positive")
    return [r / total for r in ratios]


def find_tg_column(columns: Iterable[str]) -> str:
    normalized = {str(c).strip(): c for c in columns}
    for candidate in TG_COLUMN_CANDIDATES:
        if candidate in normalized:
            return str(normalized[candidate])
    lowered = {str(c).strip().lower(): c for c in columns}
    for key, original in lowered.items():
        if "glass" in key or key == "tg":
            return str(original)
    raise KeyError("Could not find glass-transition/Tg column")


def load_smp_records(path: str | Path, sheet_name: str | int | None = 0) -> list[SMPRecord]:
    df = pd.read_excel(path, sheet_name=sheet_name)
    tg_col = find_tg_column(df.columns)
    records: list[SMPRecord] = []
    for idx, row in df.iterrows():
        raw_smiles = parse_smiles_set(row.get("Smiles"))
        smiles = [s for s in (canonicalize_smiles(s) for s in raw_smiles) if s]
        if not smiles:
            continue
        try:
            ratios = parse_ratios(row.get("Molar ratio"), len(smiles))
            tg = float(row[tg_col])
        except Exception:
            continue
        if not np.isfinite(tg):
            continue
        records.append(
            SMPRecord(
                row_index=int(idx),
                author="" if pd.isna(row.get("Author")) else str(row.get("Author")),
                no="" if pd.isna(row.get("No")) else str(row.get("No")),
                names="" if pd.isna(row.get("Names")) else str(row.get("Names")),
                smiles=tuple(smiles),
                ratios=tuple(ratios),
                tg=tg,
            )
        )
    return records


def records_to_frame(records: Iterable[SMPRecord]) -> pd.DataFrame:
    rows = []
    for rec in records:
        rows.append(
            {
                "row_index": rec.row_index,
                "author": rec.author,
                "no": rec.no,
                "names": rec.names,
                "smiles": "|".join(rec.smiles),
                "ratios": ":".join(f"{r:.8f}" for r in rec.ratios),
                "tg": rec.tg,
                "n_monomers": len(rec.smiles),
            }
        )
    return pd.DataFrame(rows)


def unique_monomers(records: Iterable[SMPRecord]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for rec in records:
        for smi in rec.smiles:
            if smi not in seen:
                seen.add(smi)
                ordered.append(smi)
    return ordered


def iter_chembl_smiles(path: str | Path, limit: int | None = None, max_length: int = 204, validate: bool = False) -> Iterator[str]:
    yielded = 0
    with Path(path).open("r", encoding="utf-8", errors="ignore", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            raw = str(row.get("canonical_smiles", "")).strip()
            if not raw or len(raw) > max_length:
                continue
            if validate:
                smi = canonicalize_smiles(raw)
                if smi is None or len(smi) > max_length:
                    continue
            else:
                smi = raw
            yield smi
            yielded += 1
            if limit is not None and yielded >= limit:
                break


def augment_smiles(smiles: Iterable[str], per_monomer: int, limit: int | None = None) -> list[str]:
    augmented: list[str] = []
    seen: set[str] = set()
    for smi in smiles:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        variants = {Chem.MolToSmiles(mol, canonical=True)}
        attempts = max(per_monomer * 4, per_monomer)
        for _ in range(attempts):
            if len(variants) >= per_monomer:
                break
            variants.add(Chem.MolToSmiles(mol, canonical=False, doRandom=True))
        for variant in variants:
            if variant in seen:
                continue
            seen.add(variant)
            augmented.append(variant)
            if limit is not None and len(augmented) >= limit:
                return augmented
    return augmented


def filter_smiles_by_charset(smiles: Iterable[str], charset: list[str], max_length: int) -> list[str]:
    allowed = set(charset)
    return [s for s in smiles if len(s) <= max_length and all(ch in allowed for ch in s)]
