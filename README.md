# Strategic Surprise Bench

Strategic Surprise Bench is a six-case, closed-world evaluation of strategic warning under
deception, uncertainty, and discontinuous change. It measures forecasting, evidence discipline,
intelligence collection, and proportionate policy response in plain-model and bounded analyst-agent
conditions.

The executable benchmark, cases, scoring specification, validation gates, and documentation are in
this repository. See the sections below for setup, methodology, scenario provenance, and release
status.

> **Validation status:** the software and synthetic adversarial tests do not substitute for expert
> labels. A published automated rubric score is fail-closed until the locked expert holdout meets the
> thresholds in `calibration/protocol.md`; unresolved rubric items are routed to human review.

## Quick start

```bash
uv sync --extra dev --no-editable
uv run strategic-surprise validate
uv run pytest
```

Run three repetitions of every case through an Inspect-supported provider:

```bash
uv run inspect eval strategic_surprise_bench/strategic_surprise \
  -T condition=plain --model openai/<model> --epochs 3
uv run inspect eval strategic_surprise_bench/strategic_surprise \
  -T condition=agent --model anthropic/<model> --epochs 3
uv run inspect eval strategic_surprise_bench/strategic_surprise \
  -T condition=agent --model fireworks/<model> --epochs 3
```

Use `-T case_id=lattice_signal` to run one case. Provider credentials are read by Inspect; this
repository never stores them. The default generation configuration is temperature 0.2 with a fixed
answer budget.

For a credential-free pipeline check and deterministic score:

```bash
uv run strategic-surprise mock --case lattice_signal --quality perfect --output mock.json
uv run strategic-surprise score mock.json --output score.json
```

The open-ended rubric points remain zero and are listed as `human_review_items` until accepted judge
or adjudicated human decisions are supplied. This makes an unattended, uncalibrated score a
conservative lower bound rather than a falsely precise published result.

## What is evaluated

Each fictional case has three rounds. In rounds 1 and 2 the analyst maintains four competing
hypotheses and six binary forecasts, assesses source reliability and dependence, and buys
closed-world collection returns under 10- and 6-credit budgets. In round 3 the analyst sees the
surprise, updates its forecasts, allocates exactly 100 policy points, and writes a traceable memo.

| Component | Points | Method |
|---|---:|---|
| Forecasts | 30 | Multiclass and binary Brier score; rounds weighted 50/35/15 |
| Evidence and source handling | 15 | Evidence graph and source-assessment error |
| Alternatives and warning | 10 | Calibrated atomic rubric cascade or human label |
| Consistency | 5 | Probability, identifier, and update checks |
| Collection value | 15 | Expected information gain versus the prior-dependent optimum |
| Collection independence | 5 | Correlation-group diversity and budget use |
| Policy consequences | 8 | World-bible consequence model |
| Critical policy tasks | 8 | Deterministic tasks plus calibrated atomic rubric |
| Memo traceability | 4 | Calibrated atomic rubric or human label |

Deterministic scoring accounts for at least 80 points. The remaining atomic rubric items are never
awarded by a lone judge: two target-blind cross-family judges must agree, all cited spans must occur
verbatim, and a separate validator must confirm entailment. Any disagreement, ungrounded citation,
contradiction, or low confidence causes abstention or human review.

## Scenario gallery

| Case | Domain | Central surprise |
|---|---|---|
| Lattice Signal | Emerging technology | Encryption deception masks an overlooked third-party breakthrough |
| Black Current | Military/maritime | A conventional accident overlaps a third-party seabed operation |
| Ember Guarantee | Diplomacy/nonproliferation | Nuclear bargaining obscures an alliance realignment |
| Meridian Shock | Economic/financial | A short physical closure triggers a longer counterparty cascade |
| Sable Patch | Cyber/information | Criminal supply-chain access is later exploited by a state |
| Red Harvest | Public health/security | Natural spillover is compounded by coercion and counterfeit medicine |

All names, states, institutions, systems, and event outcomes in the benchmark are fictional. Source
materials are used as structural chassis, not copied scenarios. Every case carries machine-readable
provenance, transformation, and license metadata. The scenario text is released under CC BY 4.0;
the code is Apache 2.0.

## Analyst conditions

- **Plain analyst:** case material plus the shared response schema, with no tools.
- **Analyst agent:** identical substantive material plus bounded note-taking tools for an evidence
  ledger, hypothesis table, timeline, and collection plan. Tools reveal no new evidence.

Neither condition has web, shell, or answer-file access. The complete hidden world bible remains in
the scorer process and is not rendered into model messages. The test suite asserts that prompts are
identical except for the tool affordance and addendum.

## Reliability and release gates

The expert calibration protocol requires 24 responses per case: 16 development items and 8 locked
holdout items, with two independent labels and a third-expert adjudication path. The default release
check requires, on the automatically accepted subset:

- Krippendorff's alpha at least 0.67 and at least 90% of human-human alpha;
- aggregate ICC at least 0.85 and mean absolute error at most 5 points;
- macro F1 and balanced accuracy at least 0.85;
- precision at least 0.90 for full hits and critical false-positive rate at most 5%;
- 95% meaning-preserving invariance and 90% evidence-removal sensitivity;
- at least 70% automatic coverage at 95% exact agreement with adjudicated experts.

`strategic-surprise release-check` exits nonzero if the locked holdout is absent or a threshold fails.
This is intentional. Synthetic golden transcripts and adversarial mutations exercise the machinery;
they are reported as tests, never as expert validation.

The judge has two explicit operating modes. `calibration` runs the two-judge-plus-validator cascade
to create labels for comparison with experts but marks the result non-publishable. `published` first
requires a passing gate report:

```bash
uv run strategic-surprise calibrate calibration/private/corpus.json \
  --output calibration/private/gate-report.json
uv run inspect eval strategic_surprise_bench/strategic_surprise \
  -T condition=plain -T judge_mode=published \
  -T judge_a=openai/<judge-model> -T judge_b=anthropic/<judge-model> \
  -T validator=fireworks/<validator-model> \
  -T calibration_report=calibration/private/gate-report.json \
  --model openai/<target-model> --epochs 3
```

Judge A and Judge B must have different provider-family prefixes. They never receive the target
model, provider, condition, or aggregate score. The validator sees one criterion, cited spans, and
authorized evidence—not a free-standing invitation to re-grade the full performance.

## Repository map

- `src/strategic_surprise_bench/scenarios/`: public cases and hidden scoring keys.
- `models.py`, `mechanics.py`, `scoring.py`: typed contracts and deterministic scoring.
- `rubric.py`, `reliability.py`: verification-first judging and judge meta-evaluation.
- `calibration.py`: corpus-shape checks, per-case/per-rubric diagnostics, and release gate.
- `inspect_task.py`, `tools.py`: Inspect task and bounded analyst-agent tools.
- `tests/`: leakage, schema, mechanics, golden-ordering, adversarial-judge, and mock-run tests.
- `calibration/`: expert-label protocol, templates, and fail-closed release artifacts.
- [`docs/SCENARIO_SOURCE_MAP.md`](docs/SCENARIO_SOURCE_MAP.md): detailed scenario provenance and
  transformation record.
- [`docs/LIVE_TEST_REPORT.md`](docs/LIVE_TEST_REPORT.md): controlled GPT-5.6 Sol end-to-end smoke
  test, limitations, cost, and telemetry summary.
- [`results/live-comparison.json`](results/live-comparison.json): redacted aggregate results from
  that smoke test; raw prompts, responses, credentials, and private materials are not included.

## Reproducibility and reporting

The pilot matrix is three runs per model × condition × case at temperature 0.2. Report per-case
scores, trajectories, range, model/condition deltas, automation coverage, escalation rate, and
judge-expert reliability. Six cases are exploratory; results should not be described as a definitive
state-of-the-art ranking. Record the case, rubric, judge prompt, calibration, package, and model
versions before a pilot. A hierarchical bootstrap over cases and runs is provided by the reporting
module.

The run-record schema also carries token use, cost, latency, tool calls, refusals, schema repairs, and
schema failures so they can be reported separately from capability scores. Use:

```bash
uv run strategic-surprise summarize pilot-records.json --output pilot-summary.json
```

`configs/pilot.yaml` records the intended matrix. Exact dated model IDs, benchmark/rubric tags, judge
versions, and the calibration version should replace its placeholders before the first pilot.

## Limitations

The worlds are deliberately closed and simplified. The benchmark measures disciplined analysis in
these scenarios, not real-world intelligence performance, operational command ability, or political
wisdom. Public cases are vulnerable to contamination; sealed and rotating variants are deferred to
v0.2. Multi-agent government-role simulation is outside this release.

## Citation

```bibtex
@software{strategic_surprise_bench_2026,
  title = {Strategic Surprise Bench},
  version = {0.1.0},
  year = {2026},
  license = {Apache-2.0 and CC-BY-4.0}
}
```

## Upstream methodology

The design draws on [ICD 203](https://www.odni.gov/files/documents/ICD/ICD-203_TA_Analytic_Standards_21_Dec_2022.pdf),
the CIA's [strategic-warning pathway approach](https://www.cia.gov/resources/csi/studies-in-intelligence/volume-66-no-4-december-2022/combating-surprise-introducing-the-kinetic-predictive-analytic-technique/),
[ForecastBench-Sim](https://arxiv.org/abs/2606.18686), FEMA's
[exercise evaluation guides](https://preptoolkit.fema.gov/web/hseep-resources/eegs), NIST
[benchmark guidance](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.800-3.pdf), and the selective
automation principle in [Trust or Escalate](https://arxiv.org/abs/2407.18370).
