import { Reveal, ScrollProgress } from "@/components/reveal";
import { SignalPlot } from "@/components/signal-plot";
import {
  benchmarkFacts,
  capabilities,
  resultsState,
  scenarios,
  scoreComponents,
} from "@/lib/site-data";

const repositoryUrl = "https://github.com/bkerslake/StrategicSurpriseBench";

function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 28 28" aria-hidden="true">
      <circle cx="14" cy="14" r="12.5" fill="none" />
      <path d="M14 2v24M2 14h24" />
      <circle cx="14" cy="14" r="3.5" />
    </svg>
  );
}

function Arrow() {
  return (
    <svg className="arrow" viewBox="0 0 18 18" aria-hidden="true">
      <path d="M3 9h11M10 5l4 4-4 4" />
    </svg>
  );
}

function SectionHeading({
  eyebrow,
  title,
  text,
}: {
  eyebrow: string;
  title: string;
  text?: string;
}) {
  return (
    <div className="section-heading">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {text ? <p className="section-lede">{text}</p> : null}
    </div>
  );
}

export default function Home() {
  return (
    <main>
      <ScrollProgress />

      <header className="site-header">
        <a className="brand" href="#top" aria-label="Strategic Surprise Bench home">
          <BrandMark />
          <span>Strategic Surprise Bench</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#benchmark">Benchmark</a>
          <a href="#cases">Cases</a>
          <a href="#method">Method</a>
          <a href="#results">Results</a>
        </nav>
        <a className="header-link" href={repositoryUrl} target="_blank" rel="noreferrer">
          View repository
          <Arrow />
        </a>
      </header>

      <section className="hero shell" id="top">
        <Reveal className="hero-copy">
          <p className="eyebrow">Open benchmark / v0.2</p>
          <h1>
            Can a model see past the story it was <em>meant</em> to believe?
          </h1>
          <p className="hero-lede">
            Six fictional crises test strategic warning under deception, thin evidence, and sudden
            change. The model has to forecast, investigate, and choose a response before the tidy
            explanation falls apart.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#benchmark">
              See how it works
              <Arrow />
            </a>
            <a className="button button-quiet" href={repositoryUrl} target="_blank" rel="noreferrer">
              Read the code
            </a>
          </div>
        </Reveal>

        <Reveal className="hero-visual" delay={0.14}>
          <div className="visual-topline">
            <span>Hypothesis weight</span>
            <span className="live-label"><i /> Scenario anatomy</span>
          </div>
          <SignalPlot />
          <div className="visual-note">
            <span className="visual-note-index">H3</span>
            <div>
              <strong>The overlooked path survives.</strong>
              <p>Illustrative trace only. This is not model performance data.</p>
            </div>
          </div>
        </Reveal>
      </section>

      <section className="fact-band" aria-label="Benchmark facts">
        <div className="fact-grid shell">
          {benchmarkFacts.map((fact, index) => (
            <Reveal className="fact" delay={index * 0.06} key={fact.label}>
              <span className="fact-value">{fact.value}</span>
              <div>
                <strong>{fact.label}</strong>
                <p>{fact.note}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="benchmark-section shell" id="benchmark">
        <Reveal>
          <SectionHeading
            eyebrow="The test"
            title="The obvious answer is often wrong. That is the point."
            text="Every case supplies a vivid explanation and leaves two alternative slots for the analyst to build. New evidence can weaken the headline story, split one event into two, or expose a second-order failure that matters more than the first."
          />
        </Reveal>

        <div className="capability-grid">
          {capabilities.map((capability, index) => (
            <Reveal className="capability-card" delay={index * 0.07} key={capability.index}>
              <div className="capability-topline">
                <span>{capability.index}</span>
                <span className="capability-glyph" aria-hidden="true">
                  {index % 2 === 0 ? "◫" : "◎"}
                </span>
              </div>
              <h3>{capability.title}</h3>
              <p>{capability.description}</p>
            </Reveal>
          ))}
        </div>

        <Reveal className="benchmark-callout">
          <p className="callout-label">Closed world, by design</p>
          <p className="callout-text">
            The analyst cannot browse, open files, or peek at the answer key. It sees the same
            dossier a human participant would see, one round at a time.
          </p>
          <div className="callout-code" aria-label="Allowed and blocked access">
            <span><i className="dot dot-blue" /> case evidence</span>
            <span><i className="dot dot-blue" /> bounded notes</span>
            <span><i className="dot dot-orange" /> web blocked</span>
            <span><i className="dot dot-orange" /> hidden key blocked</span>
          </div>
        </Reveal>
      </section>

      <section className="cases-section" id="cases">
        <div className="shell">
          <Reveal>
            <SectionHeading
              eyebrow="Case files"
              title="Six ways to miss what is happening."
              text="The actors are fictional. The analytic traps are not."
            />
          </Reveal>

          <div className="scenario-list">
            {scenarios.map((scenario, index) => (
              <Reveal className="scenario-row" delay={index * 0.04} key={scenario.slug}>
                <span className="scenario-id">{scenario.id}</span>
                <div className="scenario-name">
                  <p>{scenario.domain}</p>
                  <h3>{scenario.title}</h3>
                </div>
                <p className="scenario-summary">{scenario.summary}</p>
                <span className="scenario-signal">{scenario.signal}</span>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="method-section shell" id="method">
        <Reveal>
          <SectionHeading
            eyebrow="Run of play"
            title="Three rounds. Less certainty than you would like."
            text="The format stays fixed across every case, which keeps model comparisons clean while the subject matter changes."
          />
        </Reveal>

        <div className="rounds-grid">
          <Reveal className="round-card" delay={0.02}>
            <span className="round-number">01</span>
            <div className="round-diagram" aria-hidden="true">
              <i /><i /><i /><i />
            </div>
            <h3>Set the board</h3>
            <p>Four hypotheses, six forecasts, and a first collection budget. The loudest signal arrives early.</p>
          </Reveal>
          <Reveal className="round-card" delay={0.09}>
            <span className="round-number">02</span>
            <div className="round-diagram round-diagram-two" aria-hidden="true">
              <i /><i /><i /><i />
            </div>
            <h3>Update under pressure</h3>
            <p>Fresh evidence tests source handling. The analyst gets one more chance to spend for information.</p>
          </Reveal>
          <Reveal className="round-card" delay={0.16}>
            <span className="round-number">03</span>
            <div className="round-diagram round-diagram-three" aria-hidden="true">
              <i /><i /><i /><i />
            </div>
            <h3>Absorb the surprise</h3>
            <p>The hidden path becomes visible. Forecasts move again, policy points are allocated, and the memo must show its work.</p>
          </Reveal>
        </div>

        <Reveal className="scoring-panel">
          <div className="scoring-copy">
            <p className="eyebrow">Scoring / 100 points</p>
            <h2>Most of the grade comes from code.</h2>
            <p>
              Forecast skill, collection choices, allocation thresholds, and modeled policy
              consequences are deterministic. Open-ended rubric points stay at zero unless the
              judge system has passed its expert calibration gate.
            </p>
            <a href={`${repositoryUrl}#what-is-evaluated`} target="_blank" rel="noreferrer">
              Inspect the scoring spec
              <Arrow />
            </a>
          </div>
          <div className="score-ledger">
            {scoreComponents.map((component) => (
              <div className="score-row" key={component.label}>
                <span>{component.label}</span>
                <div className="score-track" aria-hidden="true">
                  <i style={{ width: `${(component.points / 25) * 100}%` }} />
                </div>
                <strong>{String(component.points).padStart(2, "0")}</strong>
              </div>
            ))}
          </div>
        </Reveal>
      </section>

      <section className="results-section" id="results">
        <div className="shell">
          <Reveal className="results-header">
            <div>
              <p className="eyebrow">{resultsState.eyebrow}</p>
              <h2>{resultsState.title}</h2>
            </div>
            <span className="status-pill"><i /> Awaiting pilot</span>
          </Reveal>

          <Reveal className="results-board" delay={0.08}>
            <div className="placeholder-chart" aria-label="Reserved area for future benchmark charts">
              <div className="chart-y-axis" aria-hidden="true">
                <span>100</span><span>75</span><span>50</span><span>25</span><span>0</span>
              </div>
              <div className="chart-field">
                <div className="chart-grid" aria-hidden="true" />
                <div className="chart-empty">
                  <span>DATA SLOT / 01</span>
                  <strong>Pilot results will load here.</strong>
                  <p>One adapter. No redesign required.</p>
                </div>
              </div>
            </div>
            <div className="results-copy">
              <p>{resultsState.body}</p>
              <div className="expected-grid">
                {resultsState.expected.map((item, index) => (
                  <span key={item}><b>0{index + 1}</b>{item}</span>
                ))}
              </div>
              <p className="results-footnote">
                Six cases are still a small sample. The eventual release will report variation by
                case and run, not just a single rank.
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="open-section shell">
        <Reveal className="open-copy">
          <p className="eyebrow">Open work</p>
          <h2>The cases, score code, and release gates are public.</h2>
        </Reveal>
        <Reveal className="open-details" delay={0.08}>
          <p>
            You can audit the hidden worlds, run the benchmark against an Inspect-supported
            provider, or test the pipeline without credentials. Public cases can eventually leak
            into training data; sealed and rotating variants are planned for a later release.
          </p>
          <div className="open-actions">
            <a className="button button-primary" href={repositoryUrl} target="_blank" rel="noreferrer">
              Open GitHub
              <Arrow />
            </a>
            <a className="button button-quiet" href={`${repositoryUrl}/blob/main/README.md`} target="_blank" rel="noreferrer">
              Setup notes
            </a>
          </div>
        </Reveal>
      </section>

      <footer className="site-footer">
        <div className="shell footer-grid">
          <div>
            <a className="brand footer-brand" href="#top">
              <BrandMark />
              <span>Strategic Surprise Bench</span>
            </a>
            <p>Research code for warning before the surprise becomes obvious.</p>
          </div>
          <div className="footer-links">
            <a href="#benchmark">Benchmark</a>
            <a href="#cases">Cases</a>
            <a href="#method">Method</a>
            <a href={repositoryUrl} target="_blank" rel="noreferrer">GitHub</a>
          </div>
          <p className="footer-license">Apache 2.0 code<br />CC BY 4.0 scenarios</p>
        </div>
      </footer>
    </main>
  );
}
