"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { AudioWaveform } from "@/components/AudioWaveform";
import {
  generateTrack,
  getHealth,
  listTracks,
  publishTrack,
  renderTrack,
  requestErrorMessage,
  resolveMediaUrl,
} from "@/lib/api";
import type { Health, Track } from "@/lib/api";

const models = [
  { value: "musicgen", label: "MusicGen Small", detail: "Local AI · 300M" },
] as const;

type BusyAction = "generate" | "render" | "publish" | null;

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState<"musicgen">("musicgen");
  const [duration, setDuration] = useState(8);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [publishTitle, setPublishTitle] = useState("");
  const [privacy, setPrivacy] = useState<"private" | "unlisted" | "public">("private");
  const [realUpload, setRealUpload] = useState(false);

  const activeTrack = useMemo(
    () => tracks.find((track) => track.id === selectedId) ?? tracks[0] ?? null,
    [selectedId, tracks],
  );

  const refresh = useCallback(async () => {
    try {
      const [nextHealth, nextTracks] = await Promise.all([getHealth(), listTracks()]);
      setHealth(nextHealth);
      setTracks(nextTracks);
      setSelectedId((current) => current ?? nextTracks[0]?.id ?? null);
    } catch (requestError) {
      setError(requestErrorMessage(requestError));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (activeTrack && !publishTitle) setPublishTitle(activeTrack.prompt.slice(0, 100));
  }, [activeTrack, publishTitle]);

  function replaceTrack(nextTrack: Track) {
    setTracks((current) => [nextTrack, ...current.filter((item) => item.id !== nextTrack.id)]);
    setSelectedId(nextTrack.id);
  }

  async function handleGenerate() {
    if (!prompt.trim() || busyAction) return;
    setBusyAction("generate");
    setError(null);
    setNotice(null);
    try {
      const track = await generateTrack({ prompt: prompt.trim(), model, duration_seconds: duration });
      replaceTrack(track);
      setPublishTitle(track.prompt.slice(0, 100));
      setNotice("Audio generated and saved to your local library.");
    } catch (requestError) {
      setError(requestErrorMessage(requestError));
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRender() {
    if (!activeTrack || busyAction) return;
    setBusyAction("render");
    setError(null);
    setNotice(null);
    try {
      const track = await renderTrack(activeTrack.id);
      replaceTrack(track);
      setNotice("1080p video rendered locally and is ready to preview.");
    } catch (requestError) {
      setError(requestErrorMessage(requestError));
    } finally {
      setBusyAction(null);
    }
  }

  async function handlePublish() {
    if (!activeTrack || !publishTitle.trim() || busyAction) return;
    setBusyAction("publish");
    setError(null);
    setNotice(null);
    try {
      const result = await publishTrack(activeTrack.id, {
        title: publishTitle.trim(),
        description: `${activeTrack.prompt}\n\nGenerated locally with openFlow.`,
        tags: ["openFlow", "AI music", activeTrack.model],
        privacy_status: privacy,
        dry_run: !realUpload,
      });
      replaceTrack(result.track);
      setNotice(result.message);
    } catch (requestError) {
      setError(requestErrorMessage(requestError));
    } finally {
      setBusyAction(null);
    }
  }

  const audioUrl = resolveMediaUrl(activeTrack?.audio_url ?? null);
  const videoUrl = resolveMediaUrl(activeTrack?.video_url ?? null);

  return (
    <main className="mx-auto min-h-screen max-w-[1500px] px-4 py-4 sm:px-7 lg:px-10">
      <nav className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-full bg-acid text-ink shadow-glow"><WaveIcon /></div>
          <span className="text-xl font-semibold tracking-[-0.04em]">openFlow</span>
          <span className="hidden rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-zinc-500 sm:inline">local studio</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <span className={`h-2 w-2 rounded-full ${health ? "bg-emerald-400 shadow-[0_0_10px_#34d399]" : "bg-amber-400"}`} />
          {health ? `${health.engine} · ${health.model_loaded ? health.device : `${health.device} pending`}` : "API offline"}
        </div>
      </nav>

      <section className="grid gap-6 py-7 xl:grid-cols-[minmax(0,1.15fr)_minmax(330px,0.55fr)]">
        <div className="space-y-6">
          <header className="flex flex-col justify-between gap-5 border-b border-white/10 pb-7 sm:flex-row sm:items-end">
            <div>
              <p className="mb-2 text-[10px] font-medium uppercase tracking-[0.3em] text-acid">Compose · render · publish</p>
              <h1 className="max-w-2xl text-4xl font-medium leading-none tracking-[-0.055em] text-white sm:text-6xl">A complete music pipeline on your machine.</h1>
            </div>
            <div className="flex shrink-0 gap-6 text-xs text-zinc-500">
              <div><strong className="block text-xl text-zinc-200">{health?.track_count ?? tracks.length}</strong> tracks</div>
              <div><strong className="block text-xl text-zinc-200">1080p</strong> output</div>
            </div>
          </header>

          <section className="rounded-[26px] border border-white/10 bg-panel/90 p-5 sm:p-7">
            <div className="mb-3 flex items-center justify-between">
              <label htmlFor="prompt" className="text-sm font-medium text-zinc-200">Track direction</label>
              <span className="text-xs text-zinc-600">{prompt.length}/500</span>
            </div>
            <textarea id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value.slice(0, 500))} placeholder="A slow-burning analog synth track, nocturnal and cinematic, with dusty drums and a warm bassline..." className="min-h-36 w-full resize-none rounded-2xl border border-white/10 bg-black/30 p-5 text-base leading-7 text-zinc-100 outline-none transition focus:border-acid/50 focus:ring-2 focus:ring-acid/10" />
            <div className="mt-5 grid gap-4 sm:grid-cols-[1fr_150px_auto]">
              <Control label="Generation engine">
                <select value={model} onChange={(event) => setModel(event.target.value as "musicgen")} className="control-input">
                  {models.map((item) => <option key={item.value} value={item.value}>{item.label} — {item.detail}</option>)}
                </select>
              </Control>
              <Control label="Duration">
                <select value={duration} onChange={(event) => setDuration(Number(event.target.value))} className="control-input">
                  {[4, 8, 15, 30].map((seconds) => <option key={seconds} value={seconds}>{seconds} seconds</option>)}
                </select>
              </Control>
              <button type="button" onClick={handleGenerate} disabled={!prompt.trim() || busyAction !== null} className="mt-auto h-14 min-w-44 rounded-xl bg-acid px-6 text-sm font-semibold text-ink shadow-glow transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-30">
                {busyAction === "generate" ? "Composing…" : "Generate track"}
              </button>
            </div>
          </section>

          {(error || notice) && (
            <p role={error ? "alert" : "status"} className={`rounded-xl border px-4 py-3 text-sm ${error ? "border-red-400/20 bg-red-400/5 text-red-300" : "border-acid/20 bg-acid/5 text-acid"}`}>
              {error ?? notice}
            </p>
          )}

          <TrackWorkspace
            track={activeTrack}
            audioUrl={audioUrl}
            videoUrl={videoUrl}
            busyAction={busyAction}
            publishTitle={publishTitle}
            privacy={privacy}
            realUpload={realUpload}
            onRender={handleRender}
            onPublish={handlePublish}
            onPublishTitle={setPublishTitle}
            onPrivacy={setPrivacy}
            onRealUpload={setRealUpload}
          />
        </div>

        <aside className="rounded-[26px] border border-white/10 bg-panel/70 p-4 xl:sticky xl:top-4 xl:max-h-[calc(100vh-2rem)] xl:overflow-y-auto">
          <div className="flex items-center justify-between px-2 pb-4 pt-1">
            <div><h2 className="text-sm font-medium">Local library</h2><p className="mt-1 text-xs text-zinc-600">SQLite-backed project history</p></div>
            <button type="button" onClick={() => void refresh()} className="rounded-lg border border-white/10 px-3 py-2 text-xs text-zinc-400 hover:text-white">Refresh</button>
          </div>
          <div className="space-y-2">
            {tracks.length === 0 && <div className="rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-zinc-600">No tracks yet. Generate your first take.</div>}
            {tracks.map((track, index) => (
              <button key={track.id} type="button" onClick={() => { setSelectedId(track.id); setPublishTitle(track.prompt.slice(0, 100)); }} className={`w-full rounded-2xl border p-4 text-left transition ${activeTrack?.id === track.id ? "border-acid/40 bg-acid/[0.06]" : "border-white/[0.07] bg-black/20 hover:border-white/20"}`}>
                <div className="flex items-start justify-between gap-3"><span className="line-clamp-2 text-sm leading-5 text-zinc-200">{track.prompt}</span><span className="text-[10px] text-zinc-600">#{tracks.length - index}</span></div>
                <div className="mt-4 flex items-center justify-between text-[10px] uppercase tracking-wider text-zinc-600"><span>{track.model} · {track.duration_seconds}s</span><StatusBadge track={track} /></div>
              </button>
            ))}
          </div>
        </aside>
      </section>
    </main>
  );
}

type WorkspaceProps = {
  track: Track | null;
  audioUrl?: string;
  videoUrl?: string;
  busyAction: BusyAction;
  publishTitle: string;
  privacy: "private" | "unlisted" | "public";
  realUpload: boolean;
  onRender: () => void;
  onPublish: () => void;
  onPublishTitle: (value: string) => void;
  onPrivacy: (value: "private" | "unlisted" | "public") => void;
  onRealUpload: (value: boolean) => void;
};

function TrackWorkspace(props: WorkspaceProps) {
  const { track, audioUrl, videoUrl, busyAction } = props;
  if (!track) return <section className="rounded-[26px] border border-dashed border-white/10 p-12 text-center text-zinc-600">Generated audio and publishing controls will appear here.</section>;

  return (
    <section className="overflow-hidden rounded-[26px] border border-white/10 bg-panel/90">
      <div className="border-b border-white/10 p-5 sm:p-7">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
          <div><p className="text-xs uppercase tracking-[0.2em] text-zinc-600">Active track</p><h2 className="mt-2 max-w-2xl text-xl leading-7 text-zinc-100">{track.prompt}</h2><p className="mt-2 text-xs text-zinc-600">{track.model} · {track.duration_seconds}s · {track.mocked ? "mock generator" : "AI generator"}</p></div>
          <StatusBadge track={track} />
        </div>
        <div className="mt-6"><AudioWaveform audioUrl={audioUrl} loading={busyAction === "generate"} /></div>
        <audio key={audioUrl} className="mt-4 w-full opacity-75" controls preload="metadata" src={audioUrl} />
      </div>

      <div className="grid md:grid-cols-2">
        <div className="border-b border-white/10 p-5 md:border-b-0 md:border-r sm:p-7">
          <p className="step-label">02 · Render</p>
          <h3 className="mt-2 text-lg text-zinc-100">Create the video master</h3>
          <p className="mt-2 text-sm leading-6 text-zinc-500">Merge this audio with cover art into a 1920×1080 H.264/AAC MP4.</p>
          {videoUrl ? <video key={videoUrl} className="mt-5 aspect-video w-full rounded-xl border border-white/10 bg-black" controls preload="metadata" src={videoUrl} /> : <div className="mt-5 grid aspect-video place-items-center rounded-xl border border-dashed border-white/10 bg-black/20 text-xs text-zinc-700">Video preview</div>}
          <button type="button" onClick={props.onRender} disabled={busyAction !== null || !track.audio_url} className="secondary-button mt-4 w-full">{busyAction === "render" ? "Rendering 1080p…" : track.video_url ? "Render again" : "Render 1080p video"}</button>
        </div>

        <div className="p-5 sm:p-7">
          <p className="step-label">03 · Publish</p>
          <h3 className="mt-2 text-lg text-zinc-100">Prepare YouTube upload</h3>
          <p className="mt-2 text-sm leading-6 text-zinc-500">Dry-run is the default. Real upload requires local Google OAuth configuration.</p>
          <div className="mt-5 space-y-3">
            <input value={props.publishTitle} maxLength={100} onChange={(event) => props.onPublishTitle(event.target.value)} placeholder="Video title" className="control-input" />
            <select value={props.privacy} onChange={(event) => props.onPrivacy(event.target.value as WorkspaceProps["privacy"])} className="control-input"><option value="private">Private</option><option value="unlisted">Unlisted</option><option value="public">Public</option></select>
            <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-white/10 p-3 text-xs leading-5 text-zinc-500"><input type="checkbox" checked={props.realUpload} onChange={(event) => props.onRealUpload(event.target.checked)} className="mt-1 accent-[#c7ff4a]" /><span><strong className="block text-zinc-300">Enable real YouTube upload</strong>Unchecked creates a local validation manifest only.</span></label>
          </div>
          <button type="button" onClick={props.onPublish} disabled={busyAction !== null || !track.video_url || !props.publishTitle.trim()} className={`mt-4 h-12 w-full rounded-xl text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-30 ${props.realUpload ? "bg-red-400 text-black hover:bg-red-300" : "bg-acid text-ink hover:bg-[#d5ff75]"}`}>{busyAction === "publish" ? "Publishing…" : props.realUpload ? "Upload to YouTube" : "Validate publish package"}</button>
          {track.youtube_url && <a href={track.youtube_url} target="_blank" rel="noreferrer" className="mt-3 block text-center text-sm text-acid hover:underline">Open published video ↗</a>}
        </div>
      </div>
    </section>
  );
}

function Control({ label, children }: { label: string; children: React.ReactNode }) {
  return <label><span className="mb-2 block text-[10px] uppercase tracking-[0.18em] text-zinc-500">{label}</span>{children}</label>;
}

function StatusBadge({ track }: { track: Track }) {
  const value = track.publish_status === "published" ? "published" : track.publish_status === "dry_run" ? "validated" : track.status;
  return <span className="shrink-0 rounded-full border border-white/10 px-3 py-1 text-[10px] uppercase tracking-widest text-zinc-400">{value.replace("_", " ")}</span>;
}

function WaveIcon() {
  return <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M2 10h2l1.5-5 3 10 3-12 2.5 9 1.5-4H18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}
