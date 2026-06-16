import { Badge } from "@/components/ui/badge";
import type { VideoStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

const LABELS: Record<VideoStatus, string> = {
  uploaded: "Yuklendi",
  processing: "Isleniyor",
  done: "Tamamlandi",
  failed: "Hata",
};

const TONES: Record<VideoStatus, string> = {
  uploaded: "bg-slate-200 text-slate-800 hover:bg-slate-200",
  processing: "bg-amber-100 text-amber-900 hover:bg-amber-100 animate-pulse",
  done: "bg-emerald-100 text-emerald-900 hover:bg-emerald-100",
  failed: "bg-rose-100 text-rose-900 hover:bg-rose-100",
};

export function StatusBadge({ status }: { status: VideoStatus }) {
  return (
    <Badge variant="secondary" className={cn("font-medium", TONES[status])}>
      {LABELS[status]}
    </Badge>
  );
}
