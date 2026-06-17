import { Card, CardContent } from "@/components/ui/card";
import type { Summary } from "@/lib/api";

function formatSecond(sec: number | null): string {
  if (sec === null) return "—";
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export function SummaryCards({ summary }: { summary: Summary }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <Card>
        <CardContent className="p-5">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Toplam arac
          </p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">
            {summary.total_vehicles}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Video suresi: {summary.duration_sec?.toFixed(1) ?? "—"} sn
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Tur dagilimi
          </p>
          <ul className="mt-2 space-y-1">
            {summary.label_distribution.length === 0 ? (
              <li className="text-sm text-slate-500">Tespit yok</li>
            ) : (
              summary.label_distribution.map((l) => (
                <li
                  key={l.label}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-slate-700">{l.label}</span>
                  <span className="font-semibold text-slate-900">{l.count}</span>
                </li>
              ))
            )}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            En yogun an
          </p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">
            {formatSecond(summary.busiest_second)}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {summary.busiest_second_count} arac
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
