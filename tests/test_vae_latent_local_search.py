from __future__ import annotations

import numpy as np
import pandas as pd

from trail.generation.vae_latent_local_search import canonical_smiles, prepare_replacement_pool, propose_latent_replacements_from_vectors


def test_latent_local_search_ranks_nearest_compatible_replacement() -> None:
    source = "O=C=Nc1ccccc1"
    counterpart = "NCCN"
    near_compatible = "O=C=Nc1ccc(C)cc1"
    far_compatible = "O=C=Nc1ccc(F)cc1"
    near_incompatible = "O=C(O)c1ccccc1"
    candidates = pd.DataFrame(
        [
            {
                "predicted_tg": 195.0,
                "smiles_a": source,
                "smiles_b": counterpart,
                "groups_a": "aromatic;isocyanate",
                "groups_b": "primary_amine",
            }
        ]
    )
    pool = prepare_replacement_pool(
        pd.DataFrame(
            [
                {"smiles": near_compatible, "groups": "aromatic;isocyanate", "source": "generated", "label": "near"},
                {"smiles": far_compatible, "groups": "aromatic;isocyanate", "source": "generated", "label": "far"},
                {"smiles": near_incompatible, "groups": "aromatic;carboxylic_acid", "source": "generated", "label": "acid"},
            ]
        )
    )
    vectors = {
        canonical_smiles(source): np.array([0.0, 0.0], dtype=np.float32),
        canonical_smiles(counterpart): np.array([3.0, 0.0], dtype=np.float32),
        canonical_smiles(near_compatible): np.array([0.1, 0.0], dtype=np.float32),
        canonical_smiles(far_compatible): np.array([2.0, 0.0], dtype=np.float32),
        canonical_smiles(near_incompatible): np.array([0.01, 0.0], dtype=np.float32),
    }

    proposals = propose_latent_replacements_from_vectors(
        candidates,
        pool,
        vectors,
        top_k=1,
        per_side=2,
        latent_size=2,
        vae_checkpoint="vae.pt",
        require_counterpart_compatibility=True,
    )

    assert near_incompatible not in set(proposals["replacement_smiles"])
    assert list(proposals["replacement_label"]) == ["near", "far"]
    assert list(proposals["latent_rank"]) == [1, 2]
    assert proposals.iloc[0]["feedback_constraint"] == "vae_latent_neighborhood_preserve_complementary_reactive_pair"
    assert proposals.iloc[0]["latent_distance"] < proposals.iloc[1]["latent_distance"]
    assert "isocyanate" in proposals.iloc[0]["matched_groups"]
