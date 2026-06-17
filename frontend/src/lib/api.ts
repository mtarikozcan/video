import axios from "axios";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60_000,
});

export type VideoStatus = "uploaded" | "processing" | "done" | "failed";

export interface Video {
  id: number;
  filename: string;
  s3_key: string;
  status: VideoStatus;
  job_id: string | null;
  duration_sec: number | null;
  total_vehicles: number;
  created_at: string;
}

export interface Detection {
  id: number;
  video_id: number;
  label: string;
  timestamp_ms: number;
  confidence: number;
  count: number;
}

export interface LabelCount {
  label: string;
  count: number;
}

export interface TimelineBucket {
  second: number;
  count: number;
}

export interface Summary {
  video_id: number;
  status: VideoStatus;
  total_vehicles: number;
  duration_sec: number | null;
  label_distribution: LabelCount[];
  busiest_second: number | null;
  busiest_second_count: number;
  timeline: TimelineBucket[];
}

export interface StatusResponse {
  video_id: number;
  status: VideoStatus;
  job_id: string | null;
  rekognition_status: string | null;
}

export async function listVideos(): Promise<Video[]> {
  const { data } = await api.get<Video[]>("/api/videos");
  return data;
}

export async function uploadVideo(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<Video> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<Video>("/api/videos/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
  return data;
}

export async function analyzeVideo(id: number): Promise<Video> {
  const { data } = await api.post<Video>(`/api/videos/${id}/analyze`);
  return data;
}

export async function getStatus(id: number): Promise<StatusResponse> {
  const { data } = await api.get<StatusResponse>(`/api/videos/${id}/status`);
  return data;
}

export async function getDetections(
  id: number,
  label?: string,
): Promise<Detection[]> {
  const { data } = await api.get<Detection[]>(`/api/videos/${id}/detections`, {
    params: label ? { label } : undefined,
  });
  return data;
}

export async function getSummary(id: number): Promise<Summary> {
  const { data } = await api.get<Summary>(`/api/videos/${id}/summary`);
  return data;
}

export async function deleteVideo(id: number): Promise<void> {
  await api.delete(`/api/videos/${id}`);
}
