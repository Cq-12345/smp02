# Feedback-Aware LLM/RAG Agent Packet

- provider: `offline_policy`
- prompt_hash: `aec8a5eaeb4119de`

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
RAG query: SMP target_tg_195 strict generation_feedback_strict strategy_feedback functional_group_replacement llm_rag_principle_generation llm_smiles_generation feedback-guided generation functional group compatibility expanded inventory literature_template cyanate ester maleimide isocyanate PiEvo posterior Harness
RAG refs: trail/knowledge/smp_prior_knowledge.yaml:0|trail/generation/generation_strategy_registry.yaml:0|reports/generation_failure_feedback_strict.md:3|reports/candidate_source_audit_expanded.md:7|docs/pievo_faithful_smp.md:29
RAG digest: materials_domain: thermoset_shape_memory_polymers representation_scope:   current: single_small_molecule_smiles_or_molecode   deferred:     - commodity_grade_component_mixture     - polymer_repeat_unit_hypergraph     - c || scope:   current_representation: single_small_molecule_smiles_or_molecode   deferred_representation:     - commodity_component_hypergraph     - polymer_repeat_unit_graph target:   variable_target_tg_c: true   reward_form || - Strategy feedback: `artifacts/trail/generation_feedback_strict/strategy_feedback.csv` - Failure reasons: `artifacts/trail/generation_feedback_strict/failure_reason_counts.csv` - Replacement failure groups: `artifacts/t || | source | type | authority | components | groups | top groups | | --- | --- | ---: | ---: | ---: | --- | | library | literature_dataset | 4 | 225 | 17 | ether:155;aromatic:110;ester:73;primary_amine:62;vinyl:58;epoxy:39 || - `src/smp02/pievo_faithful.py::update_posterior_full_history` - `src/smp02/pievo_faithful.py::sequential_predictive_log_likelihood` - `src/smp02/pievo_faithful.py::load_external_observations` - `src/smp02/pievo_faithful
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
- candidate_smiles: `N#COc1ccc(C(F)(F)c2ccc(OC#N)cc2)cc1|Nc1ccc(Oc2ccc(-c3ccc(Oc4ccc(N)cc4)cc3)cc2)cc1`

```json
{"smiles": ["N#COc1ccc(C(F)(F)c2ccc(OC#N)cc2)cc1", "Nc1ccc(Oc2ccc(-c3ccc(Oc4ccc(N)cc4)cc3)cc2)cc1"], "ratios": ["0.20000", "0.80000"], "feedback_constraints": "llm_smiles_generation: predictor_feedback: run VAE-WVCM/GNN predictor before recommendation.", "replacement_metadata": {"proposal_index": 56, "replace_side": "b", "replacement_source": "literature_template", "replacement_label": "template_dicyanate_fluoromethylene", "replacement_template_family": "cyanate_ester", "replacement_template_intended_group": "cyanate_ester", "counterpart_compatibility_reason": "氰酸酯-胺共反应。"}}
```
