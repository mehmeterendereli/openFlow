"use client";

import axios from "axios";
import { useEffect, useRef } from "react";

const idleBars = [22, 42, 30, 58, 76, 44, 64, 32, 52, 82, 68, 38, 72, 48, 28, 56, 74, 40, 62, 34, 52, 70, 46, 24, 44, 66, 38, 56, 30, 48, 74, 40];

type AudioWaveformProps = {
  audioUrl?: string;
  loading?: boolean;
};

export function AudioWaveform({ audioUrl, loading = false }: AudioWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!audioUrl || !canvasRef.current) return;

    let cancelled = false;
    let removeResizeListener: (() => void) | undefined;
    const audioContext = new AudioContext();

    async function renderWaveform() {
      const response = await axios.get<ArrayBuffer>(audioUrl as string, { responseType: "arraybuffer" });
      const buffer = await audioContext.decodeAudioData(response.data.slice(0));
      const samples = buffer.getChannelData(0);

      const draw = () => {
        const canvas = canvasRef.current;
        if (!canvas || cancelled) return;
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;
        const ratio = window.devicePixelRatio || 1;
        canvas.width = width * ratio;
        canvas.height = height * ratio;
        const context = canvas.getContext("2d");
        if (!context) return;
        context.scale(ratio, ratio);
        context.clearRect(0, 0, width, height);
        context.fillStyle = "#c7ff4a";

        const barCount = Math.max(36, Math.floor(width / 7));
        const bucketSize = Math.max(1, Math.floor(samples.length / barCount));
        const gap = 3;
        const barWidth = Math.max(2, width / barCount - gap);
        for (let bar = 0; bar < barCount; bar += 1) {
          let peak = 0;
          const start = bar * bucketSize;
          const end = Math.min(start + bucketSize, samples.length);
          for (let index = start; index < end; index += 12) peak = Math.max(peak, Math.abs(samples[index]));
          const barHeight = Math.max(3, peak * height * 1.6);
          context.fillRect(bar * (barWidth + gap), (height - barHeight) / 2, barWidth, barHeight);
        }
      };

      draw();
      window.addEventListener("resize", draw);
      removeResizeListener = () => window.removeEventListener("resize", draw);
    }

    renderWaveform().catch(() => undefined);
    return () => {
      cancelled = true;
      removeResizeListener?.();
      void audioContext.close();
    };
  }, [audioUrl]);

  if (!audioUrl) {
    return (
      <div aria-label="Audio waveform preview" className="flex h-20 items-center gap-[3px] overflow-hidden">
        {idleBars.map((height, index) => (
          <span
            key={index}
            className="meter-bar min-w-[3px] flex-1 rounded-full bg-zinc-700"
            style={{ height: `${height}%`, animationDelay: `${index * 35}ms`, animationPlayState: loading ? "running" : "paused" }}
          />
        ))}
      </div>
    );
  }

  return <canvas ref={canvasRef} aria-label="Generated audio waveform" className="block h-20 w-full" />;
}
