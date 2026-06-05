# Prompt/RAG Generation Packet

This packet is a reproducible stand-in for a future LLM call. It records the prompts, retrieved context refs, and candidate payloads that must be preserved when a real model is connected.

## prompt_rag_selected_001

- strategy: `llm_rag_principle_generation`
- prompt_id: `smp_rag_formula_contract_v1`
- prompt_hash: `101886fbef93bc6b`
- rag_query: `SMP target Tg 195 C functional group compatibility rigid aromatic epoxy amine cyanate ester Harness`
- rag_context_refs: `trail/knowledge/smp_prior_knowledge.yaml:0|docs/generation_strategy_and_harness.md:43|docs/generation_strategy_and_harness.md:31|docs/generation_strategy_and_harness.md:45`

Prompt:

```text
Target Tg 195.0 C within 5.0 C. Use retrieved SMP principles to propose a small-molecule formulation with explicit functional-group compatibility.
```

Candidate JSON:

```json
{"smiles": ["Nc1ccc(-c2ccc(N)c(C(F)(F)F)c2)c(C(F)(F)F)c1", "Cc1ccc(N=C=O)cc1N=C=O"], "ratios": ["0.65000", "0.35000"]}
```

## prompt_rag_selected_002

- strategy: `llm_rag_principle_generation`
- prompt_id: `smp_rag_formula_contract_v1`
- prompt_hash: `101886fbef93bc6b`
- rag_query: `SMP target Tg 195 C functional group compatibility rigid aromatic epoxy amine cyanate ester Harness`
- rag_context_refs: `trail/knowledge/smp_prior_knowledge.yaml:0|docs/generation_strategy_and_harness.md:43|docs/generation_strategy_and_harness.md:31|docs/generation_strategy_and_harness.md:45`

Prompt:

```text
Target Tg 195.0 C within 5.0 C. Use retrieved SMP principles to propose a small-molecule formulation with explicit functional-group compatibility.
```

Candidate JSON:

```json
{"smiles": ["C=CC(=O)OCCOCCOc1ccccc1", "O=C1C=CC(=O)N(c2ccc(Cc3ccc(N4C(=O)C=CC4=O)cc3)cc2)C1=O"], "ratios": ["0.30000", "0.70000"]}
```

## prompt_rag_replacement_001

- strategy: `functional_group_replacement`
- prompt_id: `replacement_audit_contract_v1`
- prompt_hash: `128702d2ed079903`
- rag_query: `SMP target Tg 195 C functional group compatibility rigid aromatic epoxy amine cyanate ester Harness`
- rag_context_refs: `trail/knowledge/smp_prior_knowledge.yaml:0|docs/generation_strategy_and_harness.md:43|docs/generation_strategy_and_harness.md:31|docs/generation_strategy_and_harness.md:45`

Prompt:

```text
Target Tg 195.0 C. Replace one component while preserving a compatible reaction pair; report the original side, replacement SMILES, and expected reaction evidence.
```

Candidate JSON:

```json
{"smiles": ["N#COc1ccc(CC2CCCC(Cc3ccc(OC#N)cc3)C2)cc1", "Nc1ccc(Oc2ccc(N)cc2)cc1"], "ratios": ["0.90000", "0.10000"]}
```

## prompt_rag_failed_001

- strategy: `llm_smiles_generation`
- prompt_id: `smp_rag_smiles_draft_contract_v1`
- prompt_hash: `0d4c9d4cb5055d0d`
- rag_query: `SMP target Tg 195 C functional group compatibility rigid aromatic epoxy amine cyanate ester Harness`
- rag_context_refs: `trail/knowledge/smp_prior_knowledge.yaml:0|docs/generation_strategy_and_harness.md:43|docs/generation_strategy_and_harness.md:31|docs/generation_strategy_and_harness.md:45`

Prompt:

```text
Target Tg 195.0 C. Draft a new SMILES-level replacement from RAG context. Do not assume chemistry is valid until Harness checks it.
```

Candidate JSON:

```json
{"smiles": ["Cc1ccc(N=C=O)cc1N=C=O", "Cc1cc(C)c(C(=O)P(=O)(c2ccccc2)c2ccccc2)c(C)c1"], "ratios": [0.5, 0.5]}
```
