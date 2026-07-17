"use client";

import { useRef, useState } from "react";
import { compact, dateFr } from "@/lib/format";

type Point = { date: string; total: number };

const W = 1000, H = 300;
const M = { top: 16, right: 16, bottom: 28, left: 78 };
const PW = W - M.left - M.right;
const PH = H - M.top - M.bottom;

/** Graphique en aires SVG. Carré, sans bordure, palette marine. */
export function AreaChart({ points }: { points: Point[] }) {
  const ref = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);

  const n = points.length;
  const max = Math.max(...points.map((p) => p.total));
  const yMax = max * 1.08;

  const x = (i: number) => M.left + (n <= 1 ? 0 : (i / (n - 1)) * PW);
  const y = (v: number) => M.top + PH - (v / yMax) * PH;

  const line = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.total).toFixed(1)}`).join(" ");
  const area = `${line} L${x(n - 1).toFixed(1)},${M.top + PH} L${x(0).toFixed(1)},${M.top + PH} Z`;

  // graduations Y (5 lignes)
  const yTicks = Array.from({ length: 5 }, (_, k) => (yMax / 4) * k);

  // étiquettes X : un repère par changement d'année
  const xTicks: { i: number; label: string }[] = [];
  let lastYear = "";
  points.forEach((p, i) => {
    const yr = p.date.slice(0, 4);
    if (yr !== lastYear) { xTicks.push({ i, label: yr }); lastYear = yr; }
  });

  function onMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = ref.current!.getBoundingClientRect();
    const vbX = ((e.clientX - rect.left) / rect.width) * W;
    if (vbX < M.left || vbX > W - M.right) { setHover(null); return; }
    const t = (vbX - M.left) / PW;
    setHover(Math.max(0, Math.min(n - 1, Math.round(t * (n - 1)))));
  }

  const hp = hover != null ? points[hover] : null;

  return (
    <div className="relative">
      <svg
        ref={ref}
        viewBox={`0 0 ${W} ${H}`}
        className="w-full h-auto select-none"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      >
        {/* graduations horizontales */}
        {yTicks.map((v, k) => (
          <g key={k}>
            <line x1={M.left} x2={W - M.right} y1={y(v)} y2={y(v)} stroke="#E4E4E7" strokeWidth={1} />
            <text x={M.left - 8} y={y(v) + 4} textAnchor="end" fontSize={11} fill="#A1A1AA">
              {compact(v)}
            </text>
          </g>
        ))}

        {/* aire + ligne */}
        <path d={area} fill="#1F4E79" fillOpacity={0.1} />
        <path d={line} fill="none" stroke="#1F4E79" strokeWidth={2} strokeLinejoin="round" />

        {/* étiquettes années */}
        {xTicks.map(({ i, label }) => (
          <text key={label} x={x(i)} y={H - 8} textAnchor="middle" fontSize={11} fill="#71717A">
            {label}
          </text>
        ))}

        {/* curseur de survol */}
        {hp && (
          <g>
            <line x1={x(hover!)} x2={x(hover!)} y1={M.top} y2={M.top + PH} stroke="#1F4E79" strokeWidth={1} strokeDasharray="3 3" />
            <rect x={x(hover!) - 3} y={y(hp.total) - 3} width={6} height={6} fill="#1F4E79" />
          </g>
        )}
      </svg>

      {/* infobulle (carrée, sans bordure) */}
      {hp && (
        <div
          className="absolute top-2 bg-primary-800 text-white px-3 py-2 text-xs pointer-events-none"
          style={{ left: `calc(${(x(hover!) / W) * 100}% )`, transform: "translateX(-50%)" }}
        >
          <div className="text-primary-200">{dateFr(hp.date)}</div>
          <div className="font-bold tabular-nums">{compact(hp.total)} FCFA</div>
        </div>
      )}
    </div>
  );
}
