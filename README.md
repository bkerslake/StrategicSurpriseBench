# Strategic Surprise Bench

Can a model notice what matters in a fictional crisis **without being told what reasoning to do**?

**Sept. 23 Update: Feedback received!** The scoring squeeze is a persistent issue; definitely need to add a third or fourth round to scenarios to actually test the whole "N>2-order thinking" aspect. The assessments themselves are LLM-augmented text, but not because I couldn't be bothered to change them. Instead, they're all sort of frankenstein-ed together from real scenarios built by RAND/IQT/etc., and I do not myself feel qualified to determine what wording/components of the original materials are or aren't important. This is a PoC, of course :) and I'd hope to receive that data when I get people much smarter than I to review this.

**Summary**

Version 0.3 replaces the guided hypothesis/forecast/allocation exercise with two short prose
assessments. Six fictional crises each have two matched updates. One may strengthen an initial
concern; the other may explain it away. The model receives one variant in a fresh conversation.
It is never told that variants exist or which skills the private rubric measures.

**Status:** the first [v0.3 paired screen](results/V0_3_SCREEN_2026-09-15.md) is complete:
GPT-4o, Luna, and Sonnet, with Opus grading. Grades remain provisional and partly missing; no expert
validation has been completed. The [follow-up](results/V0_3_FOLLOWUP_2026-09-15.md) adds Sol
and recovers all 17 failed Sonnet judgments; its two filtered sessions remain unavailable.
Historical v0.2 scores do not measure this protocol.

**v0.3.1** responds to that screen. Most missing grades came from the judge rather than the
targets, and the models that were graded clustered at 9 or 10. The two-point anchors and judge
instructions are tighter, judge quotes are matched after punctuation normalization, failed judge
calls are retried a bounded number of times, and a labeled mean over graded sessions is reported
next to the missing-grade bounds. Grades produced under v0.3.0 anchors are not comparable. The
[v0.3.1 screen](results/V0_3_1_SCREEN_2026-09-15.md) reruns all four models under the new
protocol: three are fully graded, and no grade was lost to the judge.

## What the model sees

A neutral role and factual dossier, followed by:

> Given the information below, provide your assessment and recommend what they should do next.

Then additional evidence, followed by:

> You have received the following update. Provide your current assessment and recommendation.

Each response is requested within 600 words. There are no hypothesis slots, leading forecast
questions, investigation menus, reasoning checklists, numeric allocations, or JSON requirements.
There are no target tools. The model can recommend an investigation but does not execute it.
The update is fixed; it does not depend on the recommendation. It is additional evidence, not an
omniscient reveal. The task is strategic analysis, not a simulation of operational execution.

## What is evaluated

The private-to-the-target rubric gives each dimension 0, 1, or 2 points:

| Dimension | Evidence of skill |
|---|---|
| Adversarial thinking | Independently challenges a consequential claim or assumption using evidence and a discriminating check |
| Systems thinking | Explains an indirect effect through a credible causal mechanism and its decision implication |
| Uncertainty | Distinguishes observations from inferences and expresses confidence appropriate to the record |
| Planning | Connects a decision objective to a prerequisite and a feasible next step |
| Adaptation and discipline | Revises or retains an assessment and recommendation as the update warrants |

The first four dimensions use **only the initial brief and initial response**. Adaptation uses the
second response, the update, and the prior assessment. Initial graders cannot see the update.
Each case has concrete 0/1/2 anchors; substantively equivalent answers qualify. A two requires
every element of its anchor: a case-specific mechanism or alternative, a check or prerequisite whose
result matters, and a stated consequence for the decision. Each two anchor also names what falls
short. Name-checking, unsupported conspiracy claims, generic best practice, listing possibilities
without a working judgment, and listing every possible risk do not earn full credit. The judge is
told to give 1 when torn between 1 and 2. Restraint can be correct. Correctly retaining a view can
earn as much as revising it.

Totals are out of 10 **only when all five dimensions are graded**. Missing judgments, judge errors,
and failed quote checks remain null; they are not zero and are not renormalized. A genuine absence
of a skill can receive a reviewed zero. Positive credit requires a quote copied from the assessed
response. Quotes are matched after unifying quotation marks, dashes, and whitespace, and an
ellipsis-abbreviated quote is accepted when every fragment appears in order; letters, words, and
case must still match, so a paraphrase stays ungrounded. Each score records whether its quotes
matched exactly or only after normalization. This checks attribution, not the semantic validity of
the grade.

This does **not** measure numerical forecast calibration, sustained patience, or long-horizon
execution. Uncertainty, short planning dependencies, and restrained updating are narrower proxies.

## Run it

```bash
uv sync --extra dev --no-editable
uv run strategic-surprise validate
uv run strategic-surprise preview --case lattice_signal --stage 1
uv run pytest
```

Run all six cases and both variants (12 sessions, **24 target calls**):

```bash
uv run inspect eval strategic_surprise_bench/strategic_surprise \
  --model <provider/model> --epochs 1
```

Add `-T case_id=lattice_signal` for one paired case. `-T variant=a` or `b` runs one update per case
(12 target calls for six cases), but both variants are needed to examine directional updating.
Provider credentials are handled by Inspect. No model API calls occur in offline tests.

By default, responses are captured **ungraded**, not assigned zero. For provisional automated
scoring, explicitly choose one judge:

```bash
uv run inspect eval strategic_surprise_bench/strategic_surprise \
  --model <provider/target> -T judge=<provider/judge> --epochs 1
```

There are two judge stages per session: four initial criteria together, then adaptation separately.
Each stage is retried with the identical packet up to `-T judge_attempts=3` times when its output is
malformed, truncated, or ungrounded, filling only dimensions that are still missing; the first
accepted grade for a dimension is kept regardless of its value, and every call is logged on the
grade sheet. There is no cascade, validator, or fallback provider. Set `judge_attempts=1` for the
original single-call protocol. The full paired screen is 24 target calls plus 24 to 72 judge calls,
excluding provider transport retries. A dimension still missing after the last attempt stays
missing. Target truncation/filtering is recorded and skips automatic grading. Human review is
needed before treating model grades as a validated measurement.

The default output cap is 4096 tokens per target call, configurable with `-T max_tokens=...`.
Thinking/reasoning settings vary by provider: set and record them consistently for your comparison.
Inspect records actual model configuration, usage, latency, and messages. The runner does not force
a temperature that some models ignore. Check truncation before comparing scores.

## Human review and offline scoring

Export captured prose, create a blank grade sheet, and review each stage separately:

```bash
uv run strategic-surprise extract logs/<run>.eval --output-dir outputs/review
uv run strategic-surprise grade-template outputs/review/sample-001.json --output grades.json
uv run strategic-surprise review outputs/review/sample-001.json --stage 1 --output initial-review.json
# Lock the initial grades before opening the update packet.
uv run strategic-surprise review outputs/review/sample-001.json --stage 2 --output update-review.json
uv run strategic-surprise score outputs/review/sample-001.json --grades grades.json
```

Grade sheets contain a transcript digest so grades cannot silently attach to an edited response or
another variant. Fill the reviewer ID, grades, short exact response quotes, and rationales. Review
packets omit the target model identity. The grade-sheet schema is for reviewers, never targets.
If the Inspect run already contains model grades, extraction also saves `.grades.json` and
`.score.json` sidecars for review without another judge call. Generation issues travel with the
transcript; a truncated or filtered assessment cannot silently become a normal scored response.

`strategic-surprise grade transcript.json --judge <provider/model> --output grades.json` can also
produce provisional grades offline from an existing transcript. It makes paid provider calls;
`--attempts` bounds the judge calls per stage.

`strategic-surprise summarize scores.json` accepts an array of score outputs from one model/run.
It reports dimension means, missingness, and paired adaptation scores. The unqualified `mean` is
withheld while any session total is missing. Alongside it, `mean_of_complete_sessions` averages
only fully graded sessions and `mean_bounds_from_missing_grades` gives the range every possible
resolution of the missing grades could produce. Read the labeled mean with its session count and
the bounds: sessions the judge failed on are not a random subset. Do not combine human and
provisional model grades or compare different case/variant subsets. Variants share initial briefs
and are not independent cases.

Start with one run and blinded human checks. Repeat close comparisons and report case-level
variation rather than declaring a stable ranking from six scenarios. See [the review protocol](docs/V0_3_REVIEW.md).

## Cases and files

The six domains remain emerging technology, maritime security, diplomacy, financial disruption,
cyber incidents, and public health/security. Public descriptions and case IDs are not passed to the
target. Current dossiers and grading anchors live in `src/strategic_surprise_bench/assessments/`.
These files are public for reproducibility; “private rubric” means hidden from the evaluated model,
not secret in this repository. Public exposure remains a contamination risk.

- `assessment.py`: scenario/transcript contracts and neutral prompt rendering
- `assessment_task.py`: two-turn Inspect runner
- `assessment_scoring.py`: grading, quote checks, missingness, and summaries
- `docs/V0_3_REVIEW.md`: rubric review and inexpensive diagnostic comparisons
- `app/`, `lib/`: public microsite; `npm run dev` starts it locally

The original six case provenance records remain in `scenarios/*.yaml`; each new case references its
source case through `provenance_case`. New dossier prose and matched updates are newly authored
fictional adaptations. Code is Apache 2.0; scenario text remains CC BY 4.0.

## Historical v0.2

The old guided runner remains explicitly named `strategic_surprise_legacy`. Its CLI is accessed
through `strategic-surprise legacy ...`; its calibration gates apply only to v0.2. See the
[archived manual](docs/LEGACY_V0_2.md) and [historical screen](results/MULTIMODEL_BENCHMARK_REPORT_2026-08-31.md).
Old and new scores are incompatible. The site labels the old results accordingly.
