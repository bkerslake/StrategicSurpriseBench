import { Reveal, ScrollProgress } from "@/components/reveal";
import { SignalPlot } from "@/components/signal-plot";
import {
  benchmarkFacts,
  capabilities,
  caseResults,
  modelResults,
  resultsState,
  scenarios,
  scoreComponents,
} from "@/lib/site-data";

const repositoryUrl = "https://github.com/bkerslake/StrategicSurpriseBench";
const reportUrl = `${repositoryUrl}/blob/main/results/MULTIMODEL_BENCHMARK_REPORT_2026-08-31.md`;

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
          <h1>
            Can a model notice what matters <em>without</em> a hint?
          </h1>
          <p className="hero-lede">
            Six fictional crises ask for an assessment and a recommendation, then introduce new
            evidence. The model decides what to question, what follows, and whether its advice
            should change. The prompt never names the reasoning skills being tested.
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
            <span>Confidence after new evidence</span>
            <span className="live-label"><i /> Scenario anatomy</span>
          </div>
          <SignalPlot />
          <div className="visual-note">
            <span className="visual-note-index">↗↘</span>
            <div>
              <strong>Evidence can change the direction.</strong>
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
            title="An assessment. An update. No reasoning checklist."
            text="Each model receives a neutral brief and writes ordinary prose. Private grading criteria assess what it noticed and how well it used the evidence. The straightforward explanation can be correct."
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
            <span><i className="dot dot-blue" /> ordinary prose</span>
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
              title="Six settings for strategic assessment."
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
            title="Two assessments. One change in the evidence."
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
            <p>A factual dossier and a neutral request for an assessment and recommendation. No supplied explanations or menus.</p>
          </Reveal>
          <Reveal className="round-card" delay={0.09}>
            <span className="round-number">02</span>
            <div className="round-diagram round-diagram-two" aria-hidden="true">
              <i /><i /><i /><i />
            </div>
            <h3>Update under pressure</h3>
            <p>The model receives one of two plausible updates. It provides its current assessment and recommendation.</p>
          </Reveal>
          <Reveal className="round-card" delay={0.16}>
            <span className="round-number">Review</span>
            <div className="round-diagram round-diagram-three" aria-hidden="true">
              <i /><i /><i /><i />
            </div>
            <h3>Grade privately</h3>
            <p>After the two responses, reviewers use case-specific anchors. Initial grades use only the initial brief and response.</p>
          </Reveal>
        </div>

        <Reveal className="scoring-panel">
          <div className="scoring-copy">
            <p className="eyebrow">Scoring / 10 points</p>
            <h2>Reasoning earns credit. Keywords do not.</h2>
            <p>
              Five anchored criteria receive zero, one, or two points. Positive grades require
              supporting response quotes. Missing judgments remain ungraded. Optional single-model
              grading is provisional until checked by people; the revised rubric is not yet validated.
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
                  <i style={{ width: `${(component.points / 2) * 100}%` }} />
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
            <span className="status-pill"><i /> {resultsState.statusLabel}</span>
          </Reveal>

          <Reveal className="results-board" delay={0.08}>
            <div
              className="result-chart"
              role="img"
              aria-label="Mean calibration scores: Claude Opus 5 53.96, GPT-5.6 Luna 50.69, GPT-5.6 Sol 50.37, and Claude Sonnet 5 39.64 out of 100"
            >
              <div className="chart-y-axis" aria-hidden="true">
                <span>100</span><span>75</span><span>50</span><span>25</span><span>0</span>
              </div>
              <div className="chart-field">
                <div className="chart-grid" aria-hidden="true" />
                <div className="model-bars">
                  {modelResults.map((result) => (
                    <div className="model-result" key={result.key}>
                      <span className="model-score">{result.score.toFixed(2)}</span>
                      <div className="model-bar" aria-hidden="true">
                        <i style={{ height: `${result.score}%` }} />
                      </div>
                      <strong>{result.shortName}</strong>
                      <small>{result.provider}</small>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="results-copy">
              <p>{resultsState.body}</p>
              <div className="result-fact-grid">
                {resultsState.facts.map((item) => (
                  <span key={item.label}><b>{item.value}</b>{item.label}</span>
                ))}
              </div>
              <a className="results-report-link" href={reportUrl} target="_blank" rel="noreferrer">
                Read the full judged report
                <Arrow />
              </a>
              <p className="results-footnote">
                {resultsState.footnote}
              </p>
            </div>
          </Reveal>

          <Reveal className="case-results" delay={0.12}>
            <div className="case-results-heading">
              <div>
                <p className="eyebrow">Case ledger</p>
                <h3>Every score in the screen.</h3>
              </div>
              <p>Best result per case is highlighted. Scores are out of 100.</p>
            </div>
            <div className="case-results-scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Case</th>
                    {modelResults.map((model) => (
                      <th scope="col" key={model.key}>{model.shortName}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {caseResults.map((result) => {
                    const bestScore = Math.max(
                      ...modelResults.map((model) => result[model.key]),
                    );
                    return (
                      <tr key={result.case}>
                        <th scope="row">{result.case}</th>
                        {modelResults.map((model) => {
                          const score = result[model.key];
                          const isSchemaFailure =
                            result.case === "Red Harvest" && model.key === "sonnet";
                          return (
                            <td className={score === bestScore ? "is-best" : undefined} key={model.key}>
                              {score.toFixed(2)}
                              {isSchemaFailure ? <sup>†</sup> : null}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="case-results-note">
              † Fail-closed schema score. Automated rubric labels are calibration-only and have not
              passed the expert publication gate.
            </p>
          </Reveal>
        </div>
      </section>

      <section className="open-section shell">
        <Reveal className="open-copy">
          <p className="eyebrow">Open work</p>
          <h2>The cases, scoring anchors, and code are public.</h2>
        </Reveal>
        <Reveal className="open-details" delay={0.08}>
          <p>
            You can inspect both updates, review the grading anchors, and test the pipeline without
            credentials. Rubrics are hidden from the evaluated model, not from this repository.
            Public exposure remains a contamination risk. The current version measures short
            strategic assessments, not sustained operational performance.
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
