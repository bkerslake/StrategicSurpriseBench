const traces = [
  { d: "M 22 116 C 92 109, 150 105, 220 102 S 344 97, 438 94", color: "var(--ink-30)" },
  { d: "M 22 93 C 98 90, 156 91, 220 88 S 352 84, 438 79", color: "var(--blue-40)" },
  { d: "M 22 72 C 94 67, 160 70, 220 66 S 354 63, 438 60", color: "var(--blue-60)" },
  { d: "M 22 108 C 92 106, 152 101, 220 95 C 292 86, 348 58, 438 20", color: "var(--orange)" },
] as const;

export function SignalPlot() {
  return (
    <div className="signal-plot" role="img" aria-label="Illustration of four hypotheses changing across three scenario rounds">
      <svg viewBox="0 0 460 146" aria-hidden="true">
        {[24, 56, 88, 120].map((y) => (
          <line key={y} x1="22" y1={y} x2="438" y2={y} className="plot-grid" />
        ))}
        {[22, 220, 438].map((x) => (
          <line key={x} x1={x} y1="12" x2={x} y2="126" className="plot-grid" />
        ))}
        {traces.map((trace, index) => (
          <path
            key={trace.d}
            d={trace.d}
            pathLength="1"
            className="signal-trace"
            fill="none"
            stroke={trace.color}
            strokeWidth={index === 3 ? 3 : 1.5}
            style={{ animationDelay: `${0.2 + index * 0.12}s` }}
          />
        ))}
        <circle
          className="signal-end"
          cx="438"
          cy="20"
          r="5"
          fill="var(--orange)"
        />
      </svg>
      <div className="plot-axis" aria-hidden="true">
        <span>Round 01</span>
        <span>Round 02</span>
        <span>Round 03</span>
      </div>
    </div>
  );
}
