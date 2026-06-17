"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TimelineBucket } from "@/lib/api";

interface Props {
  timeline: TimelineBucket[];
}

export function DetectionTimeline({ timeline }: Props) {
  if (timeline.length === 0) {
    return (
      <p className="rounded border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
        Bu video icin tespit verisi yok.
      </p>
    );
  }
  return (
    <div className="rounded border border-slate-200 bg-white p-4">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={timeline} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
          <XAxis
            dataKey="second"
            tick={{ fontSize: 12, fill: "#475569" }}
            label={{
              value: "Saniye",
              position: "insideBottom",
              offset: -2,
              fill: "#64748b",
              fontSize: 12,
            }}
          />
          <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#475569" }} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 6 }}
            formatter={(v) => [`${v} arac`, "Sayi"]}
            labelFormatter={(l) => `Saniye ${l}`}
          />
          <Bar dataKey="count" fill="#334155" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
