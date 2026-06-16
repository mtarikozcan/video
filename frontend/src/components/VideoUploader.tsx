"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";

import { Button } from "@/components/ui/button";
import { uploadVideo, type Video } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props {
  onUploaded: (video: Video) => void;
}

export function VideoUploader({ onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(
    async (file: File) => {
      setError(null);
      setBusy(true);
      setProgress(0);
      try {
        const video = await uploadVideo(file, setProgress);
        onUploaded(video);
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Yukleme basarisiz";
        setError(msg);
      } finally {
        setBusy(false);
      }
    },
    [onUploaded],
  );

  const onPick = () => inputRef.current?.click();

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files?.[0];
        if (f) void upload(f);
      }}
      className={cn(
        "rounded-xl border-2 border-dashed p-10 text-center transition-colors",
        dragging
          ? "border-slate-500 bg-slate-100"
          : "border-slate-300 bg-white hover:bg-slate-50",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept="video/mp4,video/quicktime,video/x-matroska"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) void upload(f);
          e.target.value = "";
        }}
      />
      <div className="mx-auto flex max-w-md flex-col items-center gap-3">
        <div className="rounded-full bg-slate-200 p-3">
          <UploadCloud className="h-6 w-6 text-slate-700" />
        </div>
        <p className="text-base font-medium text-slate-900">
          Video dosyasini suruklebirak veya sec
        </p>
        <p className="text-sm text-slate-500">
          MP4 / MOV / MKV — analiz icin S3&apos;e yuklenecektir
        </p>
        <Button onClick={onPick} disabled={busy} className="mt-2">
          {busy ? `Yukleniyor… %${progress}` : "Dosya sec"}
        </Button>
        {busy && (
          <div className="mt-2 h-2 w-full overflow-hidden rounded bg-slate-200">
            <div
              className="h-full bg-slate-700 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
        {error && <p className="text-sm text-rose-600">{error}</p>}
      </div>
    </div>
  );
}
