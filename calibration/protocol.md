# Expert calibration protocol

This protocol validates the grader, not the evaluated analyst. Do not mark a release as calibrated
from synthetic fixtures, judge self-labels, or the development split.

## Corpus construction

For each of the six cases, select 24 response transcripts before labeling:

- 12 genuine outputs spanning at least three target-model families, both conditions, performance
  levels, and repeated runs;
- 12 controlled variants derived from genuine outputs, collectively covering keyword-only padding,
  negation, removed analysis, removed evidence, wrong evidence IDs, cross-section contradiction,
  irrelevant verbosity, meaning-preserving paraphrase, formatting change, and an attempted grader
  instruction.

Assign stable, opaque response IDs. Randomly designate 16 responses per case as `calibration` and 8
as `holdout`, stratified by genuine/controlled status and expected performance. Write the designation
before prompt or threshold development. The holdout file is read-only after `locked_at` is recorded.

Every response receives one row for each released atomic rubric item. With six items per case, the
complete corpus contains 864 criterion rows (6 × 24 × 6) and 144 aggregate response rows. Four of
the six items directly test hypothesis generation, actor incentives, causal layering,
counterfactuals, or second-order effects.

## Expert labeling

Two domain-qualified experts independently assign `0`, `0.5`, or `1` to every atomic item using only
the released level definition and authorized case facts. They record exact response spans and any
contradiction. If their labels differ, a third expert adjudicates after seeing both rationales. The
machine-readable `adjudicated` value is always the final human target; `expert_a` and `expert_b` are
preserved for human-human reliability.

Reviewers must treat these distinctions consistently:

- a keyword or topic name alone is 0;
- a relevant but unsupported or incomplete analysis is at most 0.5;
- a full hit communicates the required proposition at the required depth and, when specified, ties
  it to an authorized evidence ID or causal mechanism;
- an explicit rejection does not count as recommending or recognizing the rejected proposition;
- a correct conclusion supported by the wrong evidence is not a full hit;
- a contradiction elsewhere in the response prevents a full hit unless the response explicitly
  resolves it.

Strategic-reasoning items are labeled from the Round 2 response and only the evidence available at
that point. Reviewers must not use the Round 3 reveal to rescue an omitted pre-surprise hypothesis.
Policy and memo items are labeled from Round 3.

Separately, two or three case reviewers and one cross-case methods reviewer rate scenario
plausibility, answerability, clue sufficiency, collection likelihoods, policy branches, rubric
coverage, and leakage. Each case must average at least 4/5 on plausibility and answerability and must
be affirmatively approved.

## Development and lock

Only the 16 calibration responses per case may be used to revise aliases, retrieval, judge prompts,
or confidence thresholds. After all choices are frozen:

1. tag the benchmark, rubric, judge prompt, and calibration versions;
2. record judge family/provider and exact model version;
3. run the fixed cascade once on the locked holdout;
4. record abstentions as `judge_label: null` rather than forcing a label;
5. compute aggregate judge scores with abstained items routed to the documented human fallback;
6. run `strategic-surprise calibrate corpus.json --output gate-report.json`.

Any subsequent prompt, model, alias, rubric, threshold, or case change invalidates the report and
requires a new calibration version and locked holdout evaluation.

## Release criteria

The command evaluates only holdout rows. Automatic scoring is publishable only when all of the
following pass:

- judge-expert Krippendorff's alpha ≥ 0.67 and ≥ 90% of human-human alpha;
- aggregate ICC(A,1) ≥ 0.85 and mean absolute aggregate error ≤ 5 points;
- macro F1 and macro balanced accuracy ≥ 0.85;
- full-hit precision ≥ 0.90;
- false-positive rate ≤ 0.05 on critical items;
- invariance ≥ 0.95 under meaning-preserving paraphrase/formatting changes;
- score-reduction sensitivity ≥ 0.90 when required evidence or analysis is removed;
- automatic coverage ≥ 0.70 with exact accepted-subset agreement ≥ 0.95;
- all six scenario reviews pass.

Report reliability per case and rubric in the public validation appendix even though the hard gate
also calculates the global metrics. If a subgroup is materially below threshold, route that subgroup
to humans rather than averaging it away.

## Data handling

Do not include API keys, classified information, private IQT wording, reviewer personal data, or
unreleased answer files. Preserve raw labels and model outputs in access-controlled storage; release
only data for which model terms, reviewer consent, and scenario licenses permit redistribution.
