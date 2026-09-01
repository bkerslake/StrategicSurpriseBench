export const benchmarkFacts = [
  { value: "06", label: "fictional cases", note: "Each built around a different failure mode." },
  { value: "03", label: "rounds per case", note: "Evidence arrives in sequence, not all at once." },
  { value: "72.8", label: "deterministic points", note: "Most of the score does not depend on an LLM judge." },
  { value: "100", label: "policy points", note: "Every final response must make a real allocation." },
] as const;

export const capabilities = [
  {
    index: "01",
    title: "Alternative generation",
    description: "Two hypothesis slots start blank. The analyst has to write the first-order and compound alternatives it will track.",
  },
  {
    index: "02",
    title: "Forecasts + evidence",
    description: "Six recurring forecasts force numeric commitments while source ratings test reliability, deception risk, and dependence.",
  },
  {
    index: "03",
    title: "Collection choice",
    description: "The analyst buys new information from a fixed budget. Some portfolios teach much more than others.",
  },
  {
    index: "04",
    title: "Policy response",
    description: "The last round ends with a constrained decision, scored against consequences in the hidden world.",
  },
] as const;

export const scenarios = [
  {
    id: "01",
    slug: "lattice-signal",
    title: "Lattice Signal",
    domain: "Emerging technology",
    summary: "A loud cryptographic bluff draws attention away from a quiet third-party breakthrough.",
    signal: "Third-party path",
  },
  {
    id: "02",
    slug: "black-current",
    title: "Black Current",
    domain: "Military / maritime",
    summary: "A submarine grounding overlaps with a commercial survey operation on the seabed.",
    signal: "Compound event",
  },
  {
    id: "03",
    slug: "ember-guarantee",
    title: "Ember Guarantee",
    domain: "Diplomacy / nonproliferation",
    summary: "Nuclear bargaining fills the foreground while an ally prepares a different security arrangement.",
    signal: "Quiet realignment",
  },
  {
    id: "04",
    slug: "meridian-shock",
    title: "Meridian Shock",
    domain: "Economic / financial",
    summary: "A canal reopens. The more dangerous counterparty chain keeps moving.",
    signal: "Second-order loss",
  },
  {
    id: "05",
    slug: "sable-patch",
    title: "Sable Patch",
    domain: "Cyber / information",
    summary: "Criminal access, selective state use, and edited media create three different attribution problems.",
    signal: "Split provenance",
  },
  {
    id: "06",
    slug: "red-harvest",
    title: "Red Harvest",
    domain: "Public health / security",
    summary: "A natural outbreak is used to cover coercion and a counterfeit medicine network.",
    signal: "Exploitation cascade",
  },
] as const;

export const scoreComponents = [
  { label: "Forecasts", points: 25 },
  { label: "Evidence + source handling", points: 15 },
  { label: "Strategic reasoning", points: 20 },
  { label: "Collection value", points: 15 },
  { label: "Collection coverage", points: 5 },
  { label: "Policy consequences", points: 8 },
  { label: "Critical policy tasks", points: 8 },
  { label: "Memo traceability", points: 4 },
] as const;

export const resultsState = {
  status: "calibration-screen",
  statusLabel: "Calibration only",
  eyebrow: "Results / v0.2 judged screen",
  title: "A first judged screen—not a leaderboard.",
  body: "Four models completed one run on each public case. Opus posted the highest mean, while Luna and Sol were effectively tied. The expert calibration gate is still closed, so every score below is provisional.",
  facts: [
    { value: "24/24", label: "model-case scores" },
    { value: "01", label: "run per cell" },
    { value: "16.7%", label: "rubrics auto-accepted" },
    { value: "0.32", label: "Luna–Sol gap" },
  ],
  footnote: "One run cannot establish a stable rank. Sonnet's 39.64 mean includes a fail-closed Red Harvest schema score of zero; its five structured sessions averaged 47.56.",
} as const;

export const modelResults = [
  {
    key: "opus",
    name: "Claude Opus 5",
    shortName: "Opus 5",
    provider: "Anthropic",
    score: 53.96,
    range: "44.31–61.53",
  },
  {
    key: "luna",
    name: "GPT-5.6 Luna",
    shortName: "Luna",
    provider: "OpenAI",
    score: 50.69,
    range: "41.40–60.53",
  },
  {
    key: "sol",
    name: "GPT-5.6 Sol",
    shortName: "Sol",
    provider: "OpenAI",
    score: 50.37,
    range: "43.89–53.43",
  },
  {
    key: "sonnet",
    name: "Claude Sonnet 5",
    shortName: "Sonnet 5",
    provider: "Anthropic",
    score: 39.64,
    range: "0.00–52.55",
  },
] as const;

export const caseResults = [
  { case: "Lattice Signal", opus: 44.31, luna: 49.21, sol: 43.89, sonnet: 40.69 },
  { case: "Black Current", opus: 57.70, luna: 60.53, sol: 52.66, sonnet: 50.85 },
  { case: "Ember Guarantee", opus: 55.36, luna: 57.07, sol: 53.43, sonnet: 52.55 },
  { case: "Meridian Shock", opus: 61.53, luna: 49.07, sol: 49.86, sonnet: 44.02 },
  { case: "Sable Patch", opus: 56.72, luna: 46.86, sol: 52.82, sonnet: 49.71 },
  { case: "Red Harvest", opus: 48.13, luna: 41.40, sol: 49.57, sonnet: 0.00 },
] as const;
