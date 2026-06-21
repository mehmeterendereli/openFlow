import MockAdapter from "axios-mock-adapter";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { api, generateTrack, listTracks, publishTrack, renderTrack, resolveMediaUrl } from "./api";
import type { Track } from "./api";

const track: Track = {
  id: "track-1",
  prompt: "Nocturnal synthwave",
  model: "musicgen",
  duration_seconds: 8,
  status: "ready",
  publish_status: "not_published",
  audio_url: "/media/audio/track-1",
  video_url: null,
  youtube_url: null,
  error: null,
  mocked: false,
  created_at: "2026-06-21T00:00:00Z",
  updated_at: "2026-06-21T00:00:00Z",
};

describe("openFlow API client", () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(api);
  });

  afterEach(() => mock.restore());

  it("generates and lists tracks using the backend contract", async () => {
    mock.onPost("/generate", { prompt: track.prompt, model: "musicgen", duration_seconds: 8 }).reply(201, track);
    mock.onGet("/tracks").reply(200, [track]);

    await expect(generateTrack({ prompt: track.prompt, model: "musicgen", duration_seconds: 8 })).resolves.toEqual(track);
    await expect(listTracks()).resolves.toEqual([track]);
  });

  it("renders and publishes a selected track", async () => {
    const rendered = { ...track, status: "rendered" as const, video_url: "/media/video/track-1" };
    mock.onPost("/tracks/track-1/render").reply(200, rendered);
    mock.onPost("/tracks/track-1/publish", { title: "Night Drive", dry_run: true }).reply(200, {
      track: { ...rendered, publish_status: "dry_run" },
      mode: "dry-run",
      message: "manifest saved",
      youtube_url: null,
    });

    await expect(renderTrack("track-1")).resolves.toEqual(rendered);
    await expect(publishTrack("track-1", { title: "Night Drive", dry_run: true })).resolves.toMatchObject({ mode: "dry-run" });
  });

  it("resolves local media URLs and preserves absolute URLs", () => {
    expect(resolveMediaUrl("/media/audio/track-1")).toBe("http://localhost:8000/media/audio/track-1");
    expect(resolveMediaUrl("https://cdn.example/track.wav")).toBe("https://cdn.example/track.wav");
    expect(resolveMediaUrl(null)).toBeUndefined();
  });
});
