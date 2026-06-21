"use client";

import axios from "axios";
import { useState } from "react";

import { AudioWaveform } from "@/components/AudioWaveform";
import { generateTrack, resolveAudioUrl } from "@/lib/api";
import type { GenerationResult } from "@/lib/api";

const models = [
  { value: "ace-step", label: "ACE-Step", detail: "High fidelity" },
  { value: "musicgen", label: "MusicGen", detail: "Fast ideas" },
  { value: "rvc", label: "RVC", detail: "Voice conversion" },
] as const;

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState<GenerationResult["model"]>("ace-step");
  const [isGenerating, setIsGenerating] = useState(false);
  const [track, setTrack] = useState<GenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const audioUrl = track ? resolveAudioUrl(track.audio_url) : undefined;

  async function handleGenerate() {
    if (!prompt.trim() || isGenerating) return;
    setIsGenerating(true);
    setError(null);
    try {
      setTrack(await generateTrack({ prompt: prompt.trim(), model, duration_seconds: 8 }));
    } catch (requestError) {
      const detail = axios.isAxiosError(requestError) ? requestError.response?.data?.detail : undefined;
      setError(typeof detail === "string" ? detail : "The local generation server could not be reached.");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-[1440px] px-5 py-5 sm:px-8 lg:px-12">
      <nav className="flex items-center justify-between border-b border-white/10 pb-5">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-full bg-acid text-ink shadow-glow"><WaveIcon /></div>
          <span className="text-xl font-semibold tracking-[-0.04em]">openFlow</span>
          <span className="hidden rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-zinc-500 sm:inline">local studio</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_#34d399]" /> Engine ready
        </div>
      </nav>

      <section className="grid gap-12 py-14 lg:grid-cols-[0.82fr_1.18fr] lg:items-start lg:py-20">
        <header className="max-w-lg">
          <p className="mb-4 text-xs font-medium uppercase tracking-[0.3em] text-acid">Compose without limits</p>
          <h1 className="text-5xl font-medium leading-[0.94] tracking-[-0.065em] text-white sm:text-7xl">Turn a thought into sound.</h1>
          <p className="mt-7 max-w-md text-base leading-7 text-zinc-400">A local-first music workstation. Describe a track, choose an engine, and keep every part of the process on your machine.</p>
          <div className="mt-10 grid grid-cols-3 gap-3 border-t border-white/10 pt-5 text-xs text-zinc-500">
            <div><strong className="block text-xl font-medium text-zinc-200">100%</strong> local</div>
            <div><strong className="block text-xl font-medium text-zinc-200">3</strong> engines</div>
            <div><strong className="block text-xl font-medium text-zinc-200">WAV</strong> output</div>
          </div>
        </header>

        <div className="rounded-[28px] border border-white/10 bg-panel/90 p-5 shadow-2xl shadow-black/30 sm:p-7">
          <div className="mb-3 flex items-center justify-between">
            <label htmlFor="prompt" className="text-sm font-medium text-zinc-200">Track direction</label>
            <span className="text-xs text-zinc-600">{prompt.length}/500</span>
          </div>
          <textarea id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value.slice(0, 500))} placeholder="A slow-burning analog synth track, nocturnal and cinematic, with dusty drums and a warm bassline..." className="min-h-44 w-full resize-none rounded-2xl border border-white/10 bg-black/30 p-5 text-base leading-7 text-zinc-100 outline-none transition focus:border-acid/50 focus:ring-2 focus:ring-acid/10" />

          <div className="mt-5 grid gap-4 sm:grid-cols-[1fr_auto]">
            <div>
              <label htmlFor="model" className="mb-2 block text-xs uppercase tracking-[0.18em] text-zinc-500">Generation engine</label>
              <select id="model" value={model} onChange={(event) => setModel(event.target.value as GenerationResult["model"])} className="h-14 w-full appearance-none rounded-xl border border-white/10 bg-zinc-900 px-4 pr-10 text-sm text-zinc-200 outline-none focus:border-acid/50">
                {models.map((item) => <option key={item.value} value={item.value}>{item.label} — {item.detail}</option>)}
              </select>
            </div>
            <button type="button" onClick={handleGenerate} disabled={!prompt.trim() || isGenerating} className="mt-auto h-14 min-w-44 rounded-xl bg-acid px-6 text-sm font-semibold text-ink shadow-glow transition hover:-translate-y-0.5 hover:bg-[#d5ff75] disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:translate-y-0">
              {isGenerating ? "Composing…" : "Generate track"}
            </button>
          </div>

          {error && <p role="alert" className="mt-4 rounded-xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-300">{error} Start FastAPI on port 8000 and try again.</p>}

          <div className="mt-8 rounded-2xl border border-white/10 bg-[#0a0a0b] p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-zinc-200">{track ? track.prompt : "Your generated track"}</p>
                <p className="mt-1 text-xs text-zinc-600">{isGenerating ? "Composing locally…" : track ? `${track.model} · ${track.mocked ? "mock engine" : "AI engine"}` : "Waiting for the first take"}</p>
              </div>
              <span className="rounded-full border border-white/10 px-3 py-1 text-[10px] uppercase tracking-widest text-zinc-500">{track ? `00:${String(track.duration_seconds).padStart(2, "0")}` : "00:00"}</span>
            </div>
            <div className="mt-6"><AudioWaveform audioUrl={audioUrl} loading={isGenerating} /></div>
            <audio key={audioUrl} className="mt-5 w-full opacity-70" controls preload="metadata" src={audioUrl} aria-label="Generated audio player" />
          </div>
        </div>
      </section>
    </main>
  );
}

function WaveIcon() {
  return <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M2 10h2l1.5-5 3 10 3-12 2.5 9 1.5-4H18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}
