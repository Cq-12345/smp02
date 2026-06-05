# Out-of-Library SMP Formula Agent

This note formalizes the agentic search task for SMP formulations whose components may be outside the original XLSX monomer library.

## Hypothesis Space

A formulation hypothesis is:

```text
h = (n, m_1..m_n, r_1..r_n, source_1..source_n)
```

where `n` is variable, `m_i` are canonical SMILES, `r_i` are molar fractions on the simplex, and each source is one of:

- `library`: monomer exists in `data/SMP_Dataset.xlsx`.
- `chembl`: molecule is introduced from `data/chembl_36_chemreps.txt`.
- `generated`: molecule is introduced by a rule/template generator.

The current predictor uses the same WVCM construction as the paper reproduction:

```text
x(h) = sum_i r_i * z(m_i)
Tg_hat(h) = f(x(h))
```

where `z(m_i)` is the VAE latent vector and `f` is the selected Tg predictor.

## Hard Constraints

Hard constraints are deterministic validators. They are not learned, weakened, or deleted by the PiEvo-style loop.

```text
C_hard(h) =
  valid_rdkit(m_i)
  and single_component_molecule(m_i)
  and allowed_atom_set(m_i)
  and encodable_by_vae_charset(m_i)
  and min_components <= n <= max_components
  and r_i >= r_min
  and sum_i r_i = 1
  and reactive_network_ok(h)
```

`reactive_network_ok(h)` requires a plausible functional-group reaction graph. For multi-component formulas, every major component should participate in at least one compatible reaction edge; a trace component can be non-participating only when its ratio is small. For one-component formulas, the molecule must contain a self-curing or internally compatible reactive-group pattern.

## Evolvable Soft Priors

Soft priors are empirical beliefs with confidence values:

```text
P_j = (name_j, feature_j(h), effect_j, weight_j, confidence_j)
```

Examples:

- aromatic and rigid backbones tend to raise Tg.
- imide/anhydride/cyanate/maleimide networks tend to raise Tg.
- long flexible aliphatic or PEG-like segments tend to lower Tg.
- lower OOD distance makes model predictions more credible.
- ChEMBL or generated molecules can be used if they pass hard validators and stay inside the model applicability domain.

These priors start with finite confidence, then evolve from the agent's in-silico observation history. They are not proof-level constraints.

## Objective

For a target Tg task, the target is supplied by configuration:

```text
T_target = agent_discovery.target_tg_c
```

The 250 C run is only one configured instance. The ranking objective is:

```text
score(h) =
  |mu_Tg(h) - T_target|
  + lambda_sigma * sigma_Tg(h)
  + lambda_ood * d_ood(h)
  + lambda_n * max(0, n - 2)
  - lambda_prior * sum_j confidence_j * weight_j * feature_j(h)
  - lambda_novelty * min(new_component_count(h), 2)
```

Lower score is better. The selected report also shows the direct target distance so the model score remains auditable.

## PiEvo Mapping

PiEvo's core idea is to move from a fixed-prior hypothesis search to optimization over an evolving principle space. In the original `agent_discovery` mode:

- Hypotheses are formulations `h`.
- Principles are soft priors over structural motifs, reaction families, novelty, OOD, and component-count behavior.
- The experiment surrogate is the current VAE-WVCM-GPR Tg predictor.
- The observation is `(h, Tg_hat, sigma, hard_validity, feature vector)`.
- "Anomalies" are engineering heuristics: close-to-target candidates with low prior support or high OOD/uncertainty.
- Principle augmentation can add or refine beliefs, for example that a specific out-of-library source pattern or `n>=3` blending pattern is useful for hitting the target.

Because the current loop observes only model predictions, principle updates are in-silico beliefs. Real DSC/synthesis results should override them when available.

This mode is useful for large-scale candidate triage, but it is not a faithful implementation of PiEvo's mathematical loop. The faithful version is implemented separately as `pievo_faithful`, whose state uses:

```text
p_t(P) proportional p0(P) * product_s p(y_s | h_s, P)

S_s = 1 - exp(-sqrt((y_s - mu_MAP(h_s))^2 / (sigma_MAP^2(h_s) + sigma_obs^2)))

h_t = argmin_h Delta_t(h)^2 / (I_t(h) + eps)
```

See `docs/pievo_faithful_smp.md` and `src/smp02/pievo_faithful.py`.
