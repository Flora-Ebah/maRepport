// Mini-graphe (sparkline) SVG — carré, sans bordure, marine.

export function Sparkline({ values, height = 40 }: { values: number[]; height?: number }) {
  if (!values || values.length < 2) return <div style={{ height }} />;
  const W = 240, H = height;
  const min = Math.min(...values), max = Math.max(...values);
  const span = max - min || 1;
  const x = (i: number) => (i / (values.length - 1)) * W;
  const y = (v: number) => H - ((v - min) / span) * (H - 4) - 2;
  const line = values.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `${line} L${W},${H} L0,${H} Z`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="w-full" style={{ height }}>
      <path d={area} fill="#1F4E79" fillOpacity={0.08} />
      <path d={line} fill="none" stroke="#1F4E79" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
