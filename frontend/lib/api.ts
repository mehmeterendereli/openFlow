import axios from "axios";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export const api = axios.create({
  baseURL: API_URL,
  timeout: 60_000,
  headers: { "Content-Type": "application/json" },
});

export type GenerationRequest = {
  prompt: string;
  model: "ace-step" | "musicgen" | "rvc";
  duration_seconds?: number;
};

export type GenerationResult = {
  id: string;
  prompt: string;
  model: GenerationRequest["model"];
  duration_seconds: number;
  audio_url: string;
  mocked: boolean;
};

export async function generateTrack(request: GenerationRequest): Promise<GenerationResult> {
  const { data } = await api.post<GenerationResult>("/generate", request);
  return data;
}

export function resolveAudioUrl(path: string): string {
  return path.startsWith("http://") || path.startsWith("https://") ? path : `${API_URL}${path}`;
}
