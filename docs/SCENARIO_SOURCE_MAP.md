# Strategic Surprise Bench — scenario source map

## Canonical authored scenarios

The source of truth is the six YAML files under
`src/strategic_surprise_bench/scenarios/` in the repository.

| Scenario | Domain | Structural source chassis recorded in the file |
|---|---|---|
| `lattice_signal.yaml` | Emerging technology | Private strategic-surprise workshop format; CISA Secure Tomorrow Series |
| `black_current.yaml` | Military/maritime | IQT Snow Globe; Panopticon |
| `ember_guarantee.yaml` | Diplomacy/nonproliferation | State Department International Nuclear Crisis; CIA strategic-warning materials |
| `meridian_shock.yaml` | Economic/financial | State Department Suez Canal Crisis simulation; Federal Reserve stress scenarios |
| `sable_patch.yaml` | Cyber/information | CISA Cybersecurity Scenarios; Panopticon |
| `red_harvest.yaml` | Public health/security | State Department International Ebola Response Simulation; CISA synthetic-biology foresight |

Every file begins with `manifest.provenance`. Each provenance entry records the source title and URL
when public, applicable license statement, the structural element used, and how the new scenario was
transformed. These sources are chassis and methodological inspiration; the fictional actors,
evidence order, hidden truth, causal path, observation likelihoods, forecasts, policy consequences,
and rubrics are newly authored.

## What is inside one scenario file

The YAML deliberately contains both the exercise and its answer key:

1. `manifest`, `role`, and `background`: identity, provenance, analyst role, and opening context.
2. `hypotheses`: four mutually exclusive scoring slots. The headline and null explanations are
   rendered, while H2 and H3 retain private definitions and appear as blank first-order and
   second-order/compound slots that the analyst must formulate.
3. `rounds`: the three-round schedule and common evidence released in each round.
4. `evidence`: public injects plus possible closed-world collection returns. Every item has source
   reliability, deception risk, correlation group, and support/contradiction links.
5. `collection_actions`: price, possible observation, likelihood under each hypothesis, correlation
   group, and the evidence item returned if selected.
6. `forecasts`: six recurring binary questions, horizons, resolution rules, and resolved outcomes.
7. `policy_levers`, `policy_consequences`, and `critical_tasks`: the bounded final decision and its
   scoring model.
8. `rubric`: human-authored atomic criteria for generated mechanisms, actor incentives,
   counterfactual and second-order reasoning, policy, and memo quality.
9. `world_bible`: hidden truth, resolved hypothesis, actor motives, causal pathway, and surprise type.

The prompt renderer does **not** serialize the whole YAML. It sends only the analyst-facing fields
and evidence that is common for the current round or returned by a collection action the model
actually bought. The scorer retains the world bible, resolved outcomes, observation likelihoods,
policy consequences, and atomic rubric definitions.

## Relationship to the private IQT material

The supplied private IQT correspondence and Quantum Surprise Round 2/3 injects are not included in
the release repository. They were used only to understand the exercise pattern: a steering-group
role, successive injects, deception followed by a discontinuity, and a final resource-allocation
decision.

`Lattice Signal` is the adaptation, not a renamed copy. It substitutes fictional states and
institutions, changes the evidence graph and collection decisions, makes Norland the overlooked
third-party path, pre-registers forecasts and policy consequences, and adds a machine-scored hidden
world. Its provenance entry explicitly says that private wording is not redistributed.

## Public versus hidden material

These are public v0.2 cases, so the hidden keys are inspectable in the repository after the run. At
runtime, the model has no web, shell, or file access and receives only rendered evidence. This is
adequate for an open benchmark and transparent scoring, but public cases can eventually become
contaminated. A sealed future release should physically separate public dossiers from private answer keys and
rotate evidence details while preserving the constructs being measured.
