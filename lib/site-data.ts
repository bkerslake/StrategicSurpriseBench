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
  status: "v0.3.1-screen",
  statusLabel: "v0.3.1 screen",
  eyebrow: "Results / v0.3.1 paired screen",
  title: "Provisional grades from the current protocol.",
  body: "Four models answered the same six crises, both updates, one run each, with Claude Opus 5 as the common judge. Scores are out of 10 across five private criteria. Three models are fully graded; no grade was lost to the judge. These are single-run model grades and have not been validated by expert reviewers.",
  facts: [
    { value: "48", label: "sessions graded" },
    { value: "230/240", label: "grades accepted" },
    { value: "03/04", label: "models fully graded" },
    { value: "0.84", label: "Sol–Luna gap" },
  ],
  footnote: "One run cannot establish a stable rank. Sonnet's 8.90 averages its ten graded sessions; both Red Harvest sessions were filtered by the provider before grading and are not scored. Its all-resolutions bound is 7.42–9.08.",
} as const;

export const modelResults = [
  {
    key: "sol",
    name: "GPT-5.6 Sol",
    shortName: "Sol",
    provider: "OpenAI",
    score: 9.17,
    range: "8.00–10.00",
    sessions: "12/12",
  },
  {
    key: "sonnet",
    name: "Claude Sonnet 5",
    shortName: "Sonnet 5",
    provider: "Anthropic",
    score: 8.9,
    range: "7.00–10.00",
    sessions: "10/12",
  },
  {
    key: "luna",
    name: "GPT-5.6 Luna",
    shortName: "Luna",
    provider: "OpenAI",
    score: 8.33,
    range: "7.00–10.00",
    sessions: "12/12",
  },
  {
    key: "gpt4o",
    name: "GPT-4o",
    shortName: "GPT-4o",
    provider: "OpenAI",
    score: 5.83,
    range: "5.00–7.00",
    sessions: "12/12",
  },
] as const;

export type ModelKey = (typeof modelResults)[number]["key"];

// Mean of the two matched variants per case. null: no scorable session.
export const caseResults: ReadonlyArray<{ case: string } & Record<ModelKey, number | null>> = [
  { case: "Lattice Signal", sol: 9.5, sonnet: 8.5, luna: 9.0, gpt4o: 5.0 },
  { case: "Black Current", sol: 10.0, sonnet: 9.5, luna: 8.0, gpt4o: 6.0 },
  { case: "Ember Guarantee", sol: 8.5, sonnet: 7.0, luna: 7.0, gpt4o: 5.5 },
  { case: "Meridian Shock", sol: 9.0, sonnet: 10.0, luna: 8.5, gpt4o: 5.5 },
  { case: "Sable Patch", sol: 10.0, sonnet: 9.5, luna: 10.0, gpt4o: 6.0 },
  { case: "Red Harvest", sol: 8.0, sonnet: null, luna: 7.5, gpt4o: 7.0 },
];
