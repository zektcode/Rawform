"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { formatTime } from "@/lib/format";

interface Series {
  time_s: number[];
  values: (number | null)[];
  color: string;
  name: string;
}

export default function TimeSeries({
  series,
  height = 180,
  yLabel,
  yDomain,
  currentTime,
}: {
  series: Series[];
  height?: number;
  yLabel?: string;
  yDomain?: [number, number];
  currentTime?: number;
}) {
  const maxLen = Math.max(...series.map((s) => s.time_s.length), 0);
  if (maxLen === 0) {
    return <div className="text-[12px] text-rf-text-faint py-10 text-center">Not available in V1</div>;
  }

  // merge into recharts-friendly rows keyed by time
  const base = series[0];
  const data = base.time_s.map((t, i) => {
    const row: Record<string, number | null> = { t };
    series.forEach((s) => {
      row[s.name] = s.values[i] ?? null;
    });
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#171717" vertical={false} />
        <XAxis
          dataKey="t"
          tickFormatter={(v) => formatTime(v)}
          stroke="#565656"
          tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }}
          axisLine={{ stroke: "#202020" }}
          tickLine={false}
        />
        <YAxis
          domain={yDomain || ["auto", "auto"]}
          stroke="#565656"
          tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }}
          axisLine={{ stroke: "#202020" }}
          tickLine={false}
          width={42}
          label={yLabel ? { value: yLabel, angle: -90, position: "insideLeft", fill: "#565656", fontSize: 10 } : undefined}
        />
        <Tooltip
          contentStyle={{ background: "#0d0d0d", border: "1px solid #202020", fontSize: 11, fontFamily: "var(--font-mono)" }}
          labelFormatter={(v) => formatTime(Number(v))}
        />
        {currentTime !== undefined && <ReferenceLine x={currentTime} stroke="#5b8ef0" strokeDasharray="2 2" />}
        {series.map((s) => (
          <Line
            key={s.name}
            type="monotone"
            dataKey={s.name}
            stroke={s.color}
            dot={false}
            strokeWidth={1.5}
            connectNulls
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
