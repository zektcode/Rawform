"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { BandEnergy } from "@/lib/types";

export default function BandBars({
  bands,
  height = 220,
  valueKey = "relative_energy",
  unit = "%",
  highlightAbove,
}: {
  bands: BandEnergy[];
  height?: number;
  valueKey?: "relative_energy" | "energy_db";
  unit?: string;
  highlightAbove?: number;
}) {
  if (!bands?.length) {
    return <div className="text-[12px] text-rf-text-faint py-10 text-center">Not available in V1</div>;
  }
  const data = bands.map((b) => ({
    label: b.label || `${b.range_hz[0]}-${b.range_hz[1]}`,
    value: valueKey === "relative_energy" ? b.relative_energy * 100 : b.energy_db,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#171717" vertical={false} />
        <XAxis
          dataKey="label"
          stroke="#565656"
          tick={{ fontSize: 9, fontFamily: "var(--font-mono)" }}
          axisLine={{ stroke: "#202020" }}
          tickLine={false}
          angle={-40}
          textAnchor="end"
          height={54}
          interval={0}
        />
        <YAxis
          stroke="#565656"
          tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }}
          axisLine={{ stroke: "#202020" }}
          tickLine={false}
          width={36}
        />
        <Tooltip
          contentStyle={{ background: "#0d0d0d", border: "1px solid #202020", fontSize: 11, fontFamily: "var(--font-mono)" }}
          formatter={(v) => [`${Number(v).toFixed(1)}${unit}`, "Energy"]}
        />
        <Bar dataKey="value" isAnimationActive={false}>
          {data.map((d, i) => (
            <Cell key={i} fill={highlightAbove !== undefined && d.value > highlightAbove ? "#e0645a" : "#5b8ef0"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
