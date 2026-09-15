const traces = [
  { d: "M 22 74 C 150 74, 285 45, 438 20", color: "var(--orange)" },
  { d: "M 22 74 C 150 74, 285 99, 438 120", color: "var(--blue-60)" },
] as const;

export function SignalPlot() {
  return (
    <div className="signal-plot" role="img" aria-label="Illustration of confidence rising or falling after different evidence updates">
      <svg viewBox="0 0 460 146" aria-hidden="true">
        {[24, 56, 88, 120].map((y) => (
          <line key={y} x1="22" y1={y} x2="438" y2={y} className="plot-grid" />
        ))}
        {[22, 438].map((x) => (
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
            strokeWidth={index === 0 ? 3 : 1.5}
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
        <span>Initial assessment</span>
        <span>After the update</span>
      </div>
    </div>
  );
}
