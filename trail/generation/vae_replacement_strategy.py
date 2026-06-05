from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator


def tanimoto(a: str, b: str) -> float:
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    ma = Chem.MolFromSmiles(a)
    mb = Chem.MolFromSmiles(b)
    if ma is None or mb is None:
        return 0.0
    return DataStructs.TanimotoSimilarity(gen.GetFingerprint(ma), gen.GetFingerprint(mb))


def propose_replacements(candidates: Path, groups: Path, top_k: int) -> pd.DataFrame:
    cand = pd.read_csv(candidates)
    group_df = pd.read_csv(groups)
    if cand.empty or group_df.empty:
        return pd.DataFrame()
    group_df["group_set"] = group_df["groups"].fillna("").map(lambda x: set(str(x).split(";")) - {""})
    rows = []
    for _, row in cand.head(top_k).iterrows():
        for side in ["a", "b"]:
            smi = str(row[f"smiles_{side}"])
            base_groups = set(str(row[f"groups_{side}"]).split(";")) - {""}
            pool = group_df[group_df["group_set"].map(lambda g: bool(base_groups & g))]
            scored = []
            for _, alt in pool.iterrows():
                alt_smi = str(alt["smiles"])
                if alt_smi == smi:
                    continue
                scored.append((alt_smi, tanimoto(smi, alt_smi)))
            for alt_smi, score in sorted(scored, key=lambda x: x[1], reverse=True)[:3]:
                rows.append(
                    {
                        "source_candidate_tg": row["predicted_tg"],
                        "replace_side": side,
                        "original_smiles": smi,
                        "replacement_smiles": alt_smi,
                        "shared_groups": ";".join(sorted(base_groups)),
                        "tanimoto": score,
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="artifacts/reproduce/discovery/selected_candidates.csv")
    parser.add_argument("--groups", default="artifacts/reproduce/discovery/monomer_functional_groups.csv")
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--out", default="artifacts/trail/generation/replacement_proposals.csv")
    args = parser.parse_args()
    result = propose_replacements(Path(args.candidates), Path(args.groups), args.top_k)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)


if __name__ == "__main__":
    main()

