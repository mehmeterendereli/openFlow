import axios from "axios";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export const api = axios.create({
  baseURL: API_URL,
  timeout: 120_000,
  headers: { "Content-Type": "application/json" },
});

export type ModelName = "ace-step" | "musicgen" | "rvc";
export type TrackStatus = "generating" | "ready" | "rendering" | "rendered" | "failed";
export type PublishStatus = "not_published" | "publishing" | "dry_run" | "published" | "failed";

export type GenerationRequest = {
  prompt: string;
  model: "musicgen";
  duration_seconds?: number;
};

export type Track = {
  id: string;
  prompt: string;
  model: ModelName;
  duration_seconds: number;
  status: TrackStatus;
  publish_status: PublishStatus;
  audio_url: string | null;
  video_url: string | null;
  youtube_url: string | null;
  error: string | null;
  mocked: boolean;
  created_at: string;
  updated_at: string;
};

export type Health = {
  status: "ok";
  engine: string;
  model_name: string;
  device: string;
  model_loaded: boolean;
  ffmpeg_available: boolean;
  track_count: number;
};

export type PublishRequest = {
  title: string;
  description?: string;
  tags?: string[];
  privacy_status?: "private" | "unlisted" | "public";
  dry_run?: boolean;
};

export type PublishResult = {
  track: Track;
  mode: "dry-run" | "youtube";
  message: string;
  youtube_url: string | null;
};

export async function getHealth(): Promise<Health> {
  const { data } = await api.get<Health>("/health");
  return data;
}

export async function generateTrack(request: GenerationRequest): Promise<Track> {
  const { data } = await api.post<Track>("/generate", request);
  return data;
}

export async function listTracks(): Promise<Track[]> {
  const { data } = await api.get<Track[]>("/tracks");
  return data;
}

export async function renderTrack(trackId: string): Promise<Track> {
  const { data } = await api.post<Track>(`/tracks/${trackId}/render`);
  return data;
}

export async function publishTrack(trackId: string, request: PublishRequest): Promise<PublishResult> {
  const { data } = await api.post<PublishResult>(`/tracks/${trackId}/publish`, request);
  return data;
}

export function resolveMediaUrl(path: string | null): string | undefined {
  if (!path) return undefined;
  return path.startsWith("http://") || path.startsWith("https://") ? path : `${API_URL}${path}`;
}

export function requestErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return "Unexpected local application error.";
  const detail = error.response?.data?.detail;
  return typeof detail === "string" ? detail : "The local openFlow API could not be reached.";
}
