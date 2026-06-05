from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

from smp02.utils import ensure_dir, save_json


def run_closed_loop(
    candidate_space_path: str | Path,
    out_dir: str | Path,
    iterations: int,
    top_k: int,
    target_center: float,
    uncertainty_weight: float = 0.2,
) -> pd.DataFrame:
    """Run an in-silico closed loop over predicted candidates.

    The loop treats functional-group compatibility reasons as evolvable principles.
    High-scoring candidates increase the weight of their principle in the next round,
    which narrows the search space while still preserving target-distance ranking.
    """
    out = ensure_dir(out_dir)
    df = pd.read_csv(candidate_space_path)
    if df.empty:
        empty = pd.DataFrame()
        empty.to_csv(out / "closed_loop_selected.csv", index=False)
        return empty
    df = df.copy()
    df["base_distance"] = (df["predicted_tg"] - target_center).abs()
    principle_weights: Counter[str] = Counter()
    chosen_frames = []
    used_indices: set[int] = set()
    history = []
    for iteration in range(1, iterations + 1):
        work = df.drop(index=list(used_indices), errors="ignore").copy()
        if work.empty:
            break
        prior_bonus = work["compatibility_reason"].map(lambda reason: principle_weights[str(reason)]).astype(float)
        if prior_bonus.max() > 0:
            prior_bonus = prior_bonus / prior_bonus.max()
        work["loop_score"] = work["base_distance"] - uncertainty_weight * prior_bonus
        selected = work.sort_values(["loop_score", "base_distance"]).head(top_k).copy()
        selected["iteration"] = iteration
        chosen_frames.append(selected)
        used_indices.update(selected.index.tolist())
        principle_weights.update(selected["compatibility_reason"].astype(str).tolist())
        history.append(
            {
                "iteration": iteration,
                "selected": int(len(selected)),
                "best_predicted_tg": float(selected.sort_values("base_distance").iloc[0]["predicted_tg"]),
                "principles": dict(principle_weights.most_common(10)),
            }
        )
    result = pd.concat(chosen_frames, ignore_index=True) if chosen_frames else pd.DataFrame()
    result.to_csv(out / "closed_loop_selected.csv", index=False)
    save_json(history, out / "closed_loop_history.json")
    save_json(dict(principle_weights.most_common()), out / "evolved_principles.json")
    return result

