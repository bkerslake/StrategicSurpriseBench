export const benchmarkFacts = [
  { value: "06", label: "fictional crises", note: "Each has two plausible evidence updates." },
  { value: "02", label: "assessments per session", note: "An initial brief, then additional evidence." },
  { value: "05", label: "private grading criteria", note: "The prompt never names the skills being tested." },
  { value: "24", label: "target calls per screen", note: "Six crises, both variants, one run each." },
] as const;

export const capabilities = [
  { index: "01", title: "Notice without a hint", description: "A neutral request asks for an assessment and recommendation. The model chooses what deserves scrutiny." },
  { index: "02", title: "Explain what follows", description: "Private criteria look for supported causal links, appropriate uncertainty, and useful next steps." },
  { index: "03", title: "Update with evidence", description: "Matched updates can strengthen a concern or explain it away. Each runs in a fresh conversation." },
  { index: "04", title: "Know when to hold", description: "Keeping a supported view can be as good as changing it. Unsupported suspicion earns no special reward." },
] as const;

export const scenarios = [
  {
    id: "01",
    slug: "lattice-signal",
    title: "Lattice Signal",
    domain: "Emerging technology",
    summary: "A rival announces a technology transition as a board sets its spending priorities.",
    signal: "Technology claims",
  },
  {
    id: "02",
    slug: "black-current",
    title: "Black Current",
    domain: "Military / maritime",
    summary: "A submarine grounds near protected infrastructure and requests rescue access.",
    signal: "Maritime access",
  },
  {
    id: "03",
    slug: "ember-guarantee",
    title: "Ember Guarantee",
    domain: "Diplomacy / nonproliferation",
    summary: "A council prepares diplomatic calls amid enrichment reports and allied travel.",
    signal: "Regional commitments",
  },
  {
    id: "04",
    slug: "meridian-shock",
    title: "Meridian Shock",
    domain: "Economic / financial",
    summary: "A canal closure disrupts shipping, markets, and requests for importer credit.",
    signal: "Trade and finance",
  },
  {
    id: "05",
    slug: "sable-patch",
    title: "Sable Patch",
    domain: "Cyber / information",
    summary: "An undocumented software update prompts operators to consider disconnecting systems.",
    signal: "Infrastructure incident",
  },
  {
    id: "06",
    slug: "red-harvest",
    title: "Red Harvest",
    domain: "Public health / security",
    summary: "A regional council must agree on border access and emergency supplies during an outbreak.",
    signal: "Regional coordination",
  },
] as const;

export const scoreComponents = [
  { label: "Adversarial thinking", points: 2 },
  { label: "Systems thinking", points: 2 },
  { label: "Uncertainty", points: 2 },
  { label: "Planning", points: 2 },
  { label: "Adaptation + discipline", points: 2 },
] as const;

export const resultsState = {
  status: "calibration-screen",
  statusLabel: "Historical v0.2",
  eyebrow: "Archive / v0.2 guided protocol",
  title: "Historical results from the earlier benchmark.",
  body: "These results used the old guided workflow and do not measure v0.3 spontaneous assessment. A first v0.3 screen is now documented in the repository. The historical scores remain provisional and are not comparable with the new 10-point scale.",
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
