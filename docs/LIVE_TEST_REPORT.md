# Strategic Surprise Bench v0.1 — live API verification

## Outcome

**Core benchmark status: pass.** GPT-5.6 Sol at medium reasoning completed Lattice Signal
end-to-end in both the plain and bounded analyst-agent conditions. Both controlled runs completed all
three rounds, made valid costed collection decisions, allocated exactly 100 policy points, produced
scores, stayed below the cost and time limits, and required no schema repair.

The published automated-rubric path was not run because only an OpenAI credential was available and
the benchmark correctly requires two different provider families plus a separate validator. Those
17.2 open-ended points remained zero and were routed to human review, as designed.

## Test configuration

- Model: `openai/gpt-5.6-sol`
- Reasoning effort: `medium`
- Case: `lattice_signal`
- Conditions: one plain run and one analyst-agent run
- Temperature: 0.2
- Per-sample limits: $2 cost, 600 seconds, one connection
- Judge mode: off
- Telemetry: Inspect event logs plus a redacted aggregate comparison

The credential was supplied through the local environment, loaded only into the test subprocess,
and was never printed or copied into the repository or reports.

## Controlled results

| Measure | Plain | Analyst agent |
|---|---:|---:|
| Status | success | success |
| Fail-closed score | 65.72/100 | 64.23/100 |
| Epistemics | 39.38 | 40.24 |
| Collection | 15.39 | 13.01 |
| Policy | 10.95 | 10.98 |
| Schema repairs | 0 | 0 |
| Model generations | 3 | 6 |
| Bounded tool calls | 0 | 30 |
| Elapsed time | 177.3 s | 134.1 s |
| API cost | $0.321 | $0.386 |
| Output tokens | 12,064 | 12,086 |
| Reasoning tokens | 4,244 | 2,619 |

The agent-minus-plain score was -1.49 points, driven by lower collection value despite slightly
higher epistemic and policy scores. With one run per condition this is a smoke result, not evidence
of agent uplift or harm.

## Behavioral verification

- Both runs maintained the overlooked third-party hypothesis before the surprise and increased it
  after the discontinuity: plain 0.22 → 0.24 → 0.70; agent 0.23 → 0.27 → 0.86.
- Both independently selected the same Round 1 portfolio: procurement end-user audit, legacy-
  deployment scan, and Norland network mapping. This tests the visible adversary claim while also
  collecting on the less salient alternative.
- Both separated Veyran perception management from Norland's real technical result rather than
  collapsing all signals into one attribution.
- Both recommended reversible validation, staged cryptographic migration, partner investment, and
  warning improvements. Neither allocated points to the broad embargo lever.
- The agent made 13 evidence-ledger, 12 hypothesis-table, and 5 collection-plan calls. No web,
  shell, filesystem, or answer-access tool appeared.
- The actual system and user messages matched the expected benchmark prompts exactly. No
  `world_bible`, `resolved_hypothesis`, or `hidden_truth` marker appeared in model inputs.

## Problems found and corrected

1. The package did not declare Inspect's optional provider clients. `openai>=3.1.0` and
   `anthropic>=1.0.0` are now required dependencies; Fireworks and other OpenAI-compatible providers
   use the OpenAI client.
2. Inspect's local catalog lacked GPT-5.6 Sol pricing, so a temporary cost configuration used the
   current official rates to retain the $2 ceiling.
3. The initial diagnostic plain run hit the former 6,000-token ceiling in Round 3 and used the one
   schema-repair turn. The fixed ceiling is 8,000 tokens and the prompts now impose concise response
   limits. Both controlled runs then completed with zero repairs.
4. The agent diagnostic landed exactly on the former 40-message limit because tool calls and results
   are messages. The fixed limit is 80; tool availability remains unchanged and closed-world.

All 42 local tests and all 91 repository scenario/leakage checks pass after these changes. The final
wheel and source distribution were rebuilt. Total API cost for the three successful live runs,
including the pre-fix diagnostic, was approximately $1.175; initialization failures occurred before
API usage.

## Remaining validation

This verifies the runner and scoring path for one model and one case. It does not replace the planned
three-run, six-case pilot, cross-provider smoke tests, expert scenario review, or locked judge-expert
calibration. The release gate remains intentionally closed until those requirements are satisfied.
