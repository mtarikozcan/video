"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { DetectionTimeline } from "@/components/DetectionTimeline";
import { StatusBadge } from "@/components/StatusBadge";
import { SummaryCards } from "@/components/SummaryCards";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  getDetections,
  getSummary,
  type Detection,
  type Summary,
  type VideoStatus,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const VEHICLE_LABELS = ["Car", "Truck", "Bus", "Motorcycle"];

function msToClock(ms: number): string {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  const cs = Math.floor((ms % 1000) / 10);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}.${cs
    .toString()
    .padStart(2, "0")}`;
}

export default function VideoDetailPage() {
  const params = useParams<{ id: string }>();
  const videoId = Number(params.id);

  const [summary, setSummary] = useState<Summary | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [filter, setFilter] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const [s, d] = await Promise.all([
        getSummary(videoId),
        getDetections(videoId, filter ?? undefined),
      ]);
      setSummary(s);
      setDetections(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Veri alinamadi");
    } finally {
      setLoading(false);
    }
  }, [videoId, filter]);

  useEffect(() => {
    if (Number.isFinite(videoId)) void load();
  }, [videoId, load]);

  const availableLabels = useMemo(() => {
    if (!summary) return VEHICLE_LABELS;
    const fromData = summary.object_distribution.map((l) => l.object_type);
    return Array.from(new Set([...VEHICLE_LABELS, ...fromData]));
  }, [summary]);

  const status: VideoStatus = summary?.status ?? "uploaded";

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-6 flex items-center gap-3">
        <Link href="/">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-1.5 h-4 w-4" /> Geri
          </Button>
        </Link>
        <h1 className="text-2xl font-semibold text-slate-900">
          Video #{videoId}
        </h1>
        {summary && <StatusBadge status={status} />}
      </div>

      {error && (
        <p className="mb-4 rounded border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-800">
          {error}
        </p>
      )}

      {loading || !summary ? (
        <p className="text-sm text-slate-500">Yukleniyor…</p>
      ) : (
        <>
          <section className="mb-8">
            <SummaryCards summary={summary} />
          </section>

          <section className="mb-8">
            <h2 className="mb-3 text-lg font-semibold text-slate-900">
              Zaman cizelgesi
            </h2>
            <DetectionTimeline timeline={summary.timeline} />
          </section>

          <section>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-slate-900">Tespitler</h2>
              <div className="flex flex-wrap gap-1.5">
                <FilterChip
                  active={filter === null}
                  onClick={() => setFilter(null)}
                  label="Tumu"
                />
                {availableLabels.map((l) => (
                  <FilterChip
                    key={l}
                    active={filter === l}
                    onClick={() => setFilter(l)}
                    label={l}
                  />
                ))}
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                {detections.length === 0 ? (
                  <p className="p-6 text-center text-sm text-slate-500">
                    Tespit bulunamadi.
                  </p>
                ) : (
                  <div className="max-h-[480px] overflow-auto">
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                        <tr>
                          <th className="px-4 py-2">Baslangic</th>
                          <th className="px-4 py-2">Bitis</th>
                          <th className="px-4 py-2">Tur</th>
                          <th className="px-4 py-2 text-right">Guven</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detections.map((d) => (
                          <tr
                            key={d.id}
                            className="border-t border-slate-100 hover:bg-slate-50"
                          >
                            <td className="px-4 py-2 font-mono text-slate-700">
                              {msToClock(d.timestamp_start_ms)}
                            </td>
                            <td className="px-4 py-2 font-mono text-slate-700">
                              {msToClock(d.timestamp_end_ms)}
                            </td>
                            <td className="px-4 py-2 text-slate-900">
                              {d.object_type}
                            </td>
                            <td className="px-4 py-2 text-right text-slate-700">
                              {(d.confidence * 100).toFixed(1)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </section>
        </>
      )}
    </main>
  );
}

function FilterChip({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
        active
          ? "border-slate-900 bg-slate-900 text-white"
          : "border-slate-300 bg-white text-slate-700 hover:bg-slate-100",
      )}
    >
      {label}
    </button>
  );
}
