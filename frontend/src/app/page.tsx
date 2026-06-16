"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Play, RefreshCw, Trash2 } from "lucide-react";

import { StatusBadge } from "@/components/StatusBadge";
import { VideoUploader } from "@/components/VideoUploader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  analyzeVideo,
  deleteVideo,
  getStatus,
  listVideos,
  type Video,
} from "@/lib/api";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("tr-TR");
  } catch {
    return iso;
  }
}

export default function HomePage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pollers = useRef<Map<number, ReturnType<typeof setInterval>>>(new Map());

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const data = await listVideos();
      setVideos(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Liste alinamadi");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const stopPoll = useCallback((id: number) => {
    const t = pollers.current.get(id);
    if (t) {
      clearInterval(t);
      pollers.current.delete(id);
    }
  }, []);

  const startPoll = useCallback(
    (id: number) => {
      if (pollers.current.has(id)) return;
      const t = setInterval(async () => {
        try {
          const s = await getStatus(id);
          setVideos((prev) =>
            prev.map((v) => (v.id === id ? { ...v, status: s.status } : v)),
          );
          if (s.status === "done" || s.status === "failed") stopPoll(id);
        } catch {
          // keep polling silently
        }
      }, 5000);
      pollers.current.set(id, t);
    },
    [stopPoll],
  );

  useEffect(() => {
    videos
      .filter((v) => v.status === "processing")
      .forEach((v) => startPoll(v.id));
    const pollersSnapshot = pollers.current;
    return () => {
      pollersSnapshot.forEach((t) => clearInterval(t));
      pollersSnapshot.clear();
    };
  }, [videos, startPoll]);

  const onUploaded = (v: Video) => setVideos((prev) => [v, ...prev]);

  const onAnalyze = async (id: number) => {
    try {
      const v = await analyzeVideo(id);
      setVideos((prev) => prev.map((x) => (x.id === id ? v : x)));
      startPoll(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analiz baslatilamadi");
    }
  };

  const onDelete = async (id: number) => {
    if (!confirm("Bu videoyu silmek istediginize emin misiniz?")) return;
    try {
      await deleteVideo(id);
      stopPoll(id);
      setVideos((prev) => prev.filter((v) => v.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Silme basarisiz");
    }
  };

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
            UcuncuGoz
          </h1>
          <p className="text-sm text-slate-500">
            Bulut tabanli arac tespit ve trafik analiz paneli
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void refresh()}>
          <RefreshCw className="mr-2 h-4 w-4" /> Yenile
        </Button>
      </header>

      <section className="mb-10">
        <VideoUploader onUploaded={onUploaded} />
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Videolar</h2>
        {error && (
          <p className="mb-4 rounded border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-800">
            {error}
          </p>
        )}
        {loading ? (
          <p className="text-sm text-slate-500">Yukleniyor…</p>
        ) : videos.length === 0 ? (
          <p className="text-sm text-slate-500">Henuz video yuklenmedi.</p>
        ) : (
          <div className="space-y-3">
            {videos.map((v) => (
              <Card key={v.id}>
                <CardContent className="flex flex-wrap items-center gap-4 p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-3">
                      <Link
                        href={`/videos/${v.id}`}
                        className="truncate text-base font-medium text-slate-900 hover:underline"
                      >
                        {v.filename}
                      </Link>
                      <StatusBadge status={v.status} />
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {formatDate(v.created_at)}
                      {v.duration_sec ? ` · ${v.duration_sec.toFixed(1)} sn` : ""}
                      {v.status === "done"
                        ? ` · ${v.total_vehicles} arac`
                        : ""}
                    </p>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    {(v.status === "uploaded" || v.status === "failed") && (
                      <Button size="sm" onClick={() => void onAnalyze(v.id)}>
                        <Play className="mr-1.5 h-4 w-4" /> Analizi Baslat
                      </Button>
                    )}
                    {v.status === "done" && (
                      <Link href={`/videos/${v.id}`}>
                        <Button size="sm" variant="secondary">
                          Sonuclar
                        </Button>
                      </Link>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => void onDelete(v.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
