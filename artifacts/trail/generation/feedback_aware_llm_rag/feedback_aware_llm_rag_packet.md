# Feedback-Aware LLM/RAG Agent Packet

- provider: `offline_policy`
- prompt_hash: `de8bb2bfe9dedb0e`

## Policy

```json
{
  "preferred_strategies": [
    "functional_group_replacement",
    "llm_rag_principle_generation"
  ],
  "suppressed_strategies": [
    {
      "strategy": "llm_smiles_generation",
      "pass_rate": 0.0,
      "policy_weight_delta": -0.25,
      "top_failure_reason": "prediction_missing",
      "next_constraint": "predictor_feedback: run VAE-WVCM/GNN predictor before recommendation."
    }
  ],
  "constraints": [
    "llm_smiles_generation: predictor_feedback: run VAE-WVCM/GNN predictor before recommendation."
  ],
  "policy_table": [
    {
      "strategy": "functional_group_replacement",
      "pass_rate": 1.0,
      "policy_weight_delta": 0.1,
      "top_failure_reason": "",
      "next_constraint": "retain: keep strategy in candidate generator pool."
    },
    {
      "strategy": "llm_rag_principle_generation",
      "pass_rate": 1.0,
      "policy_weight_delta": 0.1,
      "top_failure_reason": "",
      "next_constraint": "retain: keep strategy in candidate generator pool."
    },
    {
      "strategy": "llm_smiles_generation",
      "pass_rate": 0.0,
      "policy_weight_delta": -0.25,
      "top_failure_reason": "prediction_missing",
      "next_constraint": "predictor_feedback: run VAE-WVCM/GNN predictor before recommendation."
    }
  ]
}
```

## Prompt

```text
You are an SMP formulation generation agent.
Target Tg: 195.0 C, window: +/-5.0 C.
Representation scope: single small-molecule SMILES / MoleCode only.
Generate only auditable candidate records. Do not bypass RDKit, predictor, Harness, or PiEvo.
RAG query: SMP target_tg_195 strict generation_feedback_strict strategy_feedback functional_group_replacement llm_rag_principle_generation llm_smiles_generation feedback-guided generation functional group compatibility PiEvo posterior Harness
RAG refs: trail/knowledge/smp_prior_knowledge.yaml:0|trail/generation/generation_strategy_registry.yaml:0|reports/generation_failure_feedback_strict.md:3|docs/pievo_faithful_smp.md:29|reports/feedback_guided_replacement_target_sweep.md:7
RAG digest: materials_domain: thermoset_shape_memory_polymers representation_scope:   current: single_small_molecule_smiles_or_molecode   deferred:     - commodity_grade_component_mixture     - polymer_repeat_unit_hypergraph     - c || scope:   current_representation: single_small_molecule_smiles_or_molecode   deferred_representation:     - commodity_component_hypergraph     - polymer_repeat_unit_graph target:   variable_target_tg_c: true   reward_form || - Strategy feedback: `artifacts/trail/generation_feedback_strict/strategy_feedback.csv` - Failure reasons: `artifacts/trail/generation_feedback_strict/failure_reason_counts.csv` - Replacement failure groups: `artifacts/t || - `src/smp02/pievo_faithful.py::update_posterior_full_history` - `src/smp02/pievo_faithful.py::sequential_predictive_log_likelihood` - `src/smp02/pievo_faithful.py::load_external_observations` - `src/smp02/pievo_faithful || - 这一步检验“真实 Tg 不固定”：replacement 不是只为 195 C 服务，而是对每个目标重新计算 target window、reward 和 PiEvo posterior。 - strict replacement 的互补反应对约束保留在所有目标中；差异来自目标窗口和后续 PiEvo full-history posterior。 - 若某个目标的 replacement pass 很少或为 0，PiEvo 仍可运行
Generation feedback policy:
{
  "preferred_strategies": [
    "functional_group_replacement",
    "llm_rag_principle_generation"
  ],
  "suppressed_strategies": [
    {
      "strategy": "llm_smiles_generation",
      "pass_rate": 0.0,
      "policy_weight_delta": -0.25,
      "top_failure_reason": "prediction_missing",
      "next_constraint": "predictor_feedback: run VAE-WVCM/GNN predictor before recommendation."
    }
  ],
  "constraints": [
    "llm_smiles_generation: predictor_feedback: run VAE-WVCM/GNN predictor before recommendation."
  ],
  "policy_table": [
    {
      "strategy": "functional_group_replacement",
      "pass_rate": 1.0,
      "policy_weight_delta": 0.1,
      "top_failure_reason": "",
      "next_constraint": "retain: keep strategy in candidate generator pool."
    },
    {
      "strategy": "llm_rag_principle_generation",
      "pass_rate": 1.0,
      "policy_weight_delta": 0.1,
      "top_failure_reason": "",
      "next_constraint": "retain: keep strategy in candidate generator pool."
    },
    {
      "strategy": "llm_smiles_generation",
      "pass_rate": 0.0,
      "policy_weight_delta": -0.25,
      "top_failure_reason": "prediction_missing",
      "next_constraint": "predictor_feedback: run VAE-WVCM/GNN predictor before recommendation."
    }
  ]
}
Return JSON list of generation records following trail/generation/generation_record_schema.yaml.
```

## Candidate Records

### feedback_rag_selected_001

- strategy: `llm_rag_principle_generation`
- stage: `harnessed`
- candidate_smiles: `Nc1ccc(-c2ccc(N)c(C(F)(F)F)c2)c(C(F)(F)F)c1|Cc1ccc(N=C=O)cc1N=C=O`

```json
{"smiles": ["Nc1ccc(-c2ccc(N)c(C(F)(F)F)c2)c(C(F)(F)F)c1", "Cc1ccc(N=C=O)cc1N=C=O"], "ratios": ["0.65000", "0.35000"], "feedback_policy": {"preferred": ["functional_group_replacement", "llm_rag_principle_generation"], "suppressed": ["llm_smiles_generation"]}}
```

### feedback_rag_replacement_context_001

- strategy: `llm_rag_principle_generation`
- stage: `harnessed`
- candidate_smiles: `N#COc1ccc(CC2CCCC(Cc3ccc(OC#N)cc3)C2)cc1|Nc1ccc(Oc2ccc(N)cc2)cc1`

```json
{"smiles": ["N#COc1ccc(CC2CCCC(Cc3ccc(OC#N)cc3)C2)cc1", "Nc1ccc(Oc2ccc(N)cc2)cc1"], "ratios": ["0.90000", "0.10000"], "feedback_constraints": "llm_smiles_generation: predictor_feedback: run VAE-WVCM/GNN predictor before recommendation.", "replacement_metadata": {"proposal_index": 107, "replace_side": "b", "counterpart_compatibility_reason": "氰酸酯-胺共反应。"}}
```
