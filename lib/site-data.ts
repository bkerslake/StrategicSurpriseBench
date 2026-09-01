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
  status: "awaiting-pilot",
  eyebrow: "Results / reserved",
  title: "The leaderboard is intentionally empty.",
  body: "A two-run API check proved that the runner works. It did not produce a ranking. The first public charts will appear after the six-case pilot, repeated runs, and expert calibration are complete.",
  expected: ["Per-case scores", "Plain vs agent", "Uncertainty bands", "Cost + latency"],
} as const;
