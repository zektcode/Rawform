"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea } from "recharts";
import { formatHz } from "@/lib/format";

export default function SpectrumLine({
  frequencies,
  magnitudes,
  height = 260,
  highlightRange,
}: {
  frequencies: number[];
  magnitudes: number[];
  height?: number;
  highlightRange?: [number, number] | null;
}) {
  if (!frequencies?.length) {
    return <div className="text-[12px] text-rf-text-faint py-10 text-center">Not available in V1</div>;
  }
  const data = frequencies.map((f, i) => ({ f, db: magnitudes[i] }));
  const ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000].filter(
    (t) => t >= frequencies[0] && t <= frequencies[frequencies.length - 1]
  );

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#171717" vertical={false} />
        <XAxis
          dataKey="f"
          scale="log"
          domain={["dataMin", "dataMax"]}
          ticks={ticks}
          tickFormatter={(v) => formatHz(v)}
          stroke="#565656"
          tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }}
          axisLine={{ stroke: "#202020" }}
          tickLine={false}
          type="number"
        />
        <YAxis
          stroke="#565656"
          tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }}
          axisLine={{ stroke: "#202020" }}
          tickLine={false}
          width={38}
          unit="dB"
        />
        <Tooltip
          contentStyle={{ background: "#0d0d0d", border: "1px solid #202020", fontSize: 11, fontFamily: "var(--font-mono)" }}
          labelFormatter={(v) => formatHz(Number(v))}
          formatter={(v) => [`${Number(v).toFixed(1)} dB`, "Magnitude"]}
        />
        {highlightRange && <ReferenceArea x1={highlightRange[0]} x2={highlightRange[1]} fill="#e0645a" fillOpacity={0.12} />}
        <Line type="monotone" dataKey="db" stroke="#5b8ef0" dot={false} strokeWidth={1.25} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
