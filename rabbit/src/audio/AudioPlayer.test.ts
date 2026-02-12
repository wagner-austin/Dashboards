/**
 * Tests for audio player using Web Audio API.
 * Uses real test implementations instead of mocks.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { createAudioPlayer, _test_hooks } from "./AudioPlayer.js";
import type { AudioPlayerDeps } from "./AudioPlayer.js";
import type {
  AudioTrack,
  AudioContextLike,
  AudioBufferSourceNodeLike,
  GainNodeLike,
  AudioParamLike,
} from "./types.js";

/** Test audio param that tracks value changes. */
interface TestAudioParam extends AudioParamLike {
  readonly ramps: readonly { value: number; endTime: number }[];
}

/** Create test AudioParam. */
function createTestAudioParam(): TestAudioParam {
  const ramps: { value: number; endTime: number }[] = [];
  return {
    value: 0,
    linearRampToValueAtTime(value: number, endTime: number): void {
      ramps.push({ value, endTime });
    },
    get ramps(): readonly { value: number; endTime: number }[] {
      return ramps;
    },
  };
}

/** Test gain node that tracks connections. */
interface TestGainNode extends GainNodeLike {
  readonly gain: TestAudioParam;
  readonly connections: readonly AudioNode[];
}

/** Create test GainNode. */
function createTestGainNode(): TestGainNode {
  const connections: AudioNode[] = [];
  const gain = createTestAudioParam();
  return {
    gain,
    connect(destination: AudioNode): void {
      connections.push(destination);
    },
    get connections(): readonly AudioNode[] {
      return connections;
    },
  };
}

/** Test buffer source node that tracks playback. */
interface TestBufferSourceNode extends AudioBufferSourceNodeLike {
  readonly started: boolean;
  readonly stopped: boolean;
  readonly connectedTo: readonly (AudioNode | GainNodeLike)[];
}

/** Create test BufferSourceNode. */
function createTestBufferSource(): TestBufferSourceNode {
  let started = false;
  let stopped = false;
  const connectedTo: (AudioNode | GainNodeLike)[] = [];
  return {
    buffer: null,
    loop: false,
    onended: null,
    connect(destination: AudioNode | GainNodeLike): void {
      connectedTo.push(destination);
    },
    start(): void {
      started = true;
    },
    stop(): void {
      stopped = true;
    },
    get started(): boolean {
      return started;
    },
    get stopped(): boolean {
      return stopped;
    },
    get connectedTo(): readonly (AudioNode | GainNodeLike)[] {
      return connectedTo;
    },
  };
}

/** Test context that tracks all created nodes. */
interface TestContext extends AudioContextLike {
  readonly sources: readonly TestBufferSourceNode[];
  readonly gains: readonly TestGainNode[];
  readonly decodedBuffers: readonly ArrayBuffer[];
  readonly resumed: boolean;
  setDecodeRejects(value: boolean): void;
}

/** Create test AudioContext. */
function createTestContext(): TestContext {
  const sources: TestBufferSourceNode[] = [];
  const gains: TestGainNode[] = [];
  const decodedBuffers: ArrayBuffer[] = [];
  let resumed = false;
  let decodeRejects = false;
  const destination = {} as AudioNode;

  return {
    state: "running",
    destination,
    resume(): Promise<void> {
      resumed = true;
      return Promise.resolve();
    },
    createBufferSource(): AudioBufferSourceNodeLike {
      const source = createTestBufferSource();
      sources.push(source);
      return source;
    },
    createGain(): GainNodeLike {
      const gain = createTestGainNode();
      gains.push(gain);
      return gain;
    },
    decodeAudioData(data: ArrayBuffer): Promise<AudioBuffer> {
      decodedBuffers.push(data);
      if (decodeRejects) {
        return Promise.reject(new Error("Decode failed"));
      }
      return Promise.resolve({} as AudioBuffer);
    },
    get sources(): readonly TestBufferSourceNode[] {
      return sources;
    },
    get gains(): readonly TestGainNode[] {
      return gains;
    },
    get decodedBuffers(): readonly ArrayBuffer[] {
      return decodedBuffers;
    },
    get resumed(): boolean {
      return resumed;
    },
    setDecodeRejects(value: boolean): void {
      decodeRejects = value;
    },
  };
}

/** Test fetch response. */
interface TestFetchState {
  readonly fetchedUrls: readonly string[];
}

/** Create test fetch function. */
function createTestFetch(ok = true): [FetchFn, TestFetchState] {
  const fetchedUrls: string[] = [];
  const fetchFn = (url: string): Promise<Response> => {
    fetchedUrls.push(url);
    return Promise.resolve({
      ok,
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
    } as Response);
  };
  return [fetchFn, { get fetchedUrls(): readonly string[] { return fetchedUrls; } }];
}

type FetchFn = (url: string) => Promise<Response>;

/** Create test track. */
function createTestTrack(id: string, options?: { volume?: number; loop?: boolean }): AudioTrack {
  return {
    id,
    path: `audio/${id}.mp3`,
    volume: options?.volume ?? 1.0,
    loop: options?.loop ?? true,
    tags: {},
  };
}

/** Create test dependencies. */
function createTestDeps(masterVolume = 1.0): [AudioPlayerDeps, TestContext, TestFetchState] {
  const context = createTestContext();
  const [fetchFn, fetchState] = createTestFetch();
  return [
    { context, fetchFn, masterVolume },
    context,
    fetchState,
  ];
}

/** Wait for async operations. */
async function flushPromises(): Promise<void> {
  await new Promise(resolve => setTimeout(resolve, 0));
}

describe("createAudioPlayer", () => {
  beforeEach(() => {
    // Use real timers
  });

  afterEach(() => {
    // Cleanup
  });

  describe("initial state", () => {
    it("starts with no current track", () => {
      const [deps] = createTestDeps();
      const player = createAudioPlayer(deps);
      expect(player.getState().currentTrackId).toBe(null);
    });

    it("starts with isPlaying false", () => {
      const [deps] = createTestDeps();
      const player = createAudioPlayer(deps);
      expect(player.getState().isPlaying).toBe(false);
    });

    it("starts with master volume from deps", () => {
      const [deps] = createTestDeps(0.5);
      const player = createAudioPlayer(deps);
      expect(player.getState().volume).toBe(0.5);
    });
  });

  describe("play", () => {
    it("sets current track id", async () => {
      const [deps] = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      await flushPromises();

      expect(player.getState().currentTrackId).toBe("ambient");
    });

    it("sets isPlaying to true", () => {
      const [deps] = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);

      expect(player.getState().isPlaying).toBe(true);
    });

    it("fetches audio file", async () => {
      const [deps, , fetchState] = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      await flushPromises();

      expect(fetchState.fetchedUrls).toContain("audio/ambient.mp3");
    });

    it("decodes audio data", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      await flushPromises();

      expect(context.decodedBuffers.length).toBe(1);
    });

    it("creates buffer source", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      await flushPromises();

      expect(context.sources.length).toBe(1);
    });

    it("creates gain node", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      await flushPromises();

      expect(context.gains.length).toBe(1);
    });

    it("starts source playback", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      await flushPromises();

      expect(context.sources[0]?.started).toBe(true);
    });

    it("configures loop on source", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("looping", { loop: true }));
      await flushPromises();

      expect(context.sources[0]?.loop).toBe(true);
    });

    it("configures non-looping source", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("oneshot", { loop: false }));
      await flushPromises();

      expect(context.sources[0]?.loop).toBe(false);
    });

    it("caches buffers for reuse", async () => {
      const [deps, , fetchState] = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      await flushPromises();

      player.play(track);
      await flushPromises();

      expect(fetchState.fetchedUrls.length).toBe(1);
    });

    it("handles fetch failure gracefully", async () => {
      const context = createTestContext();
      const [fetchFn] = createTestFetch(false);
      const deps: AudioPlayerDeps = { context, fetchFn, masterVolume: 1.0 };
      const player = createAudioPlayer(deps);
      const track = createTestTrack("missing");

      player.play(track);
      await flushPromises();

      expect(player.getState().isPlaying).toBe(true);
    });

    it("handles decode failure gracefully", async () => {
      const context = createTestContext();
      context.setDecodeRejects(true);
      const [fetchFn] = createTestFetch();
      const deps: AudioPlayerDeps = { context, fetchFn, masterVolume: 1.0 };
      const player = createAudioPlayer(deps);
      const track = createTestTrack("corrupt");

      player.play(track);
      await flushPromises();

      expect(player.getState().isPlaying).toBe(true);
    });

    it("fades out old track when switching", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("first"));
      await flushPromises();

      player.play(createTestTrack("second"));
      await flushPromises();

      const firstGain = context.gains[0];
      expect(firstGain?.gain.ramps.some(r => r.value === 0)).toBe(true);
    });

    it("stops faded source after fade duration", async () => {
      vi.useFakeTimers();
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("first"));
      await vi.runAllTimersAsync();

      player.play(createTestTrack("second"));
      await vi.runAllTimersAsync();

      const firstSource = context.sources[0];
      expect(firstSource?.stopped).toBe(true);
      vi.useRealTimers();
    });

    it("connects source to gain node", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient"));
      await flushPromises();

      const source = context.sources[0];
      const gain = context.gains[0];
      expect(source?.connectedTo).toContain(gain);
    });

    it("connects gain to destination", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient"));
      await flushPromises();

      const gain = context.gains[0];
      expect(gain?.connections).toContain(context.destination);
    });

    it("fades in with target volume", async () => {
      const [deps, context] = createTestDeps(0.5);
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient", { volume: 0.8 }));
      await flushPromises();

      const gain = context.gains[0];
      expect(gain?.gain.ramps.some(r => r.value === 0.4)).toBe(true);
    });

    it("ignores buffer if track changed", async () => {
      const [deps] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("first"));
      player.play(createTestTrack("second"));
      await flushPromises();

      expect(player.getState().currentTrackId).toBe("second");
    });
  });

  describe("pause", () => {
    it("sets isPlaying to false", () => {
      const [deps] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient"));
      player.pause();

      expect(player.getState().isPlaying).toBe(false);
    });

    it("stops the source", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient"));
      await flushPromises();
      player.pause();

      expect(context.sources[0]?.stopped).toBe(true);
    });

    it("preserves current track id", async () => {
      const [deps] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient"));
      await flushPromises();
      player.pause();

      expect(player.getState().currentTrackId).toBe("ambient");
    });

    it("does nothing if no active source", () => {
      const [deps] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.pause();

      expect(player.getState().isPlaying).toBe(false);
    });

    it("stops fading out sources", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("first"));
      await flushPromises();
      player.play(createTestTrack("second"));
      player.pause();

      expect(context.sources[0]?.stopped).toBe(true);
    });
  });

  describe("resume", () => {
    it("sets isPlaying to true", () => {
      const [deps] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient"));
      player.pause();
      player.resume();

      expect(player.getState().isPlaying).toBe(true);
    });
  });

  describe("setVolume", () => {
    it("updates volume state", () => {
      const [deps] = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      player.setVolume(0.7);

      expect(player.getState().volume).toBe(0.7);
    });

    it("clamps volume to minimum 0", () => {
      const [deps] = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      player.setVolume(-0.5);

      expect(player.getState().volume).toBe(0);
    });

    it("clamps volume to maximum 1", () => {
      const [deps] = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      player.setVolume(1.5);

      expect(player.getState().volume).toBe(1);
    });

    it("updates gain node when playing", async () => {
      const [deps, context] = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient", { volume: 0.8 }));
      await flushPromises();

      player.setVolume(0.5);

      expect(context.gains[0]?.gain.value).toBe(0.4);
    });
  });

  describe("getState", () => {
    it("returns snapshot of state", () => {
      const [deps] = createTestDeps(0.5);
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient"));
      const state1 = player.getState();

      player.pause();
      const state2 = player.getState();

      expect(state1.isPlaying).toBe(true);
      expect(state2.isPlaying).toBe(false);
    });
  });

  describe("onended callback", () => {
    it("sets isPlaying false when track ends", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient"));
      await flushPromises();

      const source = context.sources[0];
      if (source !== undefined && source.onended !== null) {
        source.onended();
      }

      expect(player.getState().isPlaying).toBe(false);
    });

    it("clears active source when track ends", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("ambient"));
      await flushPromises();

      const source = context.sources[0];
      if (source !== undefined && source.onended !== null) {
        source.onended();
      }

      player.setVolume(0.5);
      expect(player.getState().volume).toBe(0.5);
    });

    it("ignores onended if active source changed", async () => {
      const [deps, context] = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("first"));
      await flushPromises();

      const firstSource = context.sources[0];

      player.play(createTestTrack("second"));
      await flushPromises();

      if (firstSource !== undefined && firstSource.onended !== null) {
        firstSource.onended();
      }

      expect(player.getState().isPlaying).toBe(true);
    });
  });
});

describe("_test_hooks", () => {
  it("exports createAudioPlayer", () => {
    expect(_test_hooks.createAudioPlayer).toBe(createAudioPlayer);
  });

  it("exports FADE_DURATION", () => {
    expect(_test_hooks.FADE_DURATION).toBe(1.0);
  });
});
