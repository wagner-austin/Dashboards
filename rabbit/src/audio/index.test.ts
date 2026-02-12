/**
 * Tests for audio module public API exports.
 * Uses real test implementations instead of mocks.
 */

import { describe, it, expect } from "vitest";
import {
  createAudioState,
  validateAudioConfig,
  selectTrackByTime,
  selectTrackByLocation,
  getDefaultTrack,
  createAudioPlayer,
  createBrowserAudioContext,
  createDefaultAudioDependencies,
  setupAudioStart,
  switchToNextTrack,
  setupTrackSwitcher,
  initializeAudio,
} from "./index.js";
import type {
  TimeOfDay,
  TrackTags,
  AudioTrack,
  AudioConfig,
  AudioState,
  AudioContextLike,
  AudioBufferSourceNodeLike,
  GainNodeLike,
  AudioParamLike,
  AudioPlayer,
  AudioPlayerDeps,
  AudioDependencies,
  AudioSystem,
} from "./index.js";

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

/** Test context state. */
type TestContextState = "running" | "suspended" | "closed";

/** Test context that tracks all created nodes. */
interface TestContext extends AudioContextLike {
  readonly sources: readonly TestBufferSourceNode[];
  readonly gains: readonly TestGainNode[];
}

/** Create test AudioContext. */
function createTestContext(): TestContext {
  const sources: TestBufferSourceNode[] = [];
  const gains: TestGainNode[] = [];
  const destination = {} as AudioNode;

  return {
    state: "running" as TestContextState,
    destination,
    resume(): Promise<void> {
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
    decodeAudioData(): Promise<AudioBuffer> {
      return Promise.resolve({} as AudioBuffer);
    },
    get sources(): readonly TestBufferSourceNode[] {
      return sources;
    },
    get gains(): readonly TestGainNode[] {
      return gains;
    },
  };
}

/** Create test fetch function. */
function createTestFetch(): (url: string) => Promise<Response> {
  return (url: string): Promise<Response> => {
    void url;
    return Promise.resolve({
      ok: true,
      arrayBuffer: (): Promise<ArrayBuffer> => Promise.resolve(new ArrayBuffer(8)),
    } as Response);
  };
}

describe("audio module exports", () => {
  describe("type exports", () => {
    it("exports TimeOfDay type", () => {
      const time: TimeOfDay = "day";
      expect(time).toBe("day");
    });

    it("exports TrackTags type", () => {
      const tags: TrackTags = { time: "night", location: "forest" };
      expect(tags.time).toBe("night");
    });

    it("exports AudioTrack type", () => {
      const track: AudioTrack = {
        id: "test",
        path: "audio/test.mp3",
        volume: 1.0,
        loop: true,
        tags: {},
      };
      expect(track.id).toBe("test");
    });

    it("exports AudioConfig type", () => {
      const config: AudioConfig = {
        enabled: true,
        masterVolume: 0.5,
        tracks: [],
      };
      expect(config.enabled).toBe(true);
    });

    it("exports AudioState type", () => {
      const state: AudioState = {
        currentTrackId: null,
        isPlaying: false,
        volume: 1.0,
      };
      expect(state.isPlaying).toBe(false);
    });

    it("exports AudioContextLike type", () => {
      const context: AudioContextLike = createTestContext();
      expect(context.state).toBe("running");
    });

    it("exports AudioPlayerDeps type", () => {
      const deps: AudioPlayerDeps = {
        context: createTestContext(),
        fetchFn: createTestFetch(),
        masterVolume: 1.0,
      };
      expect(deps.masterVolume).toBe(1.0);
    });
  });

  describe("function exports", () => {
    it("exports createAudioState", () => {
      const state = createAudioState();
      expect(state.currentTrackId).toBe(null);
      expect(state.isPlaying).toBe(false);
      expect(state.volume).toBe(1.0);
    });

    it("exports validateAudioConfig", () => {
      const config = validateAudioConfig({
        enabled: true,
        masterVolume: 0.5,
        tracks: [],
      });
      expect(config.enabled).toBe(true);
    });

    it("exports selectTrackByTime", () => {
      const tracks: readonly AudioTrack[] = [
        { id: "day", path: "audio/day.mp3", volume: 1.0, loop: true, tags: { time: "day" } },
      ];
      const result = selectTrackByTime(tracks, "day");
      expect(result?.id).toBe("day");
    });

    it("exports selectTrackByLocation", () => {
      const tracks: readonly AudioTrack[] = [
        { id: "forest", path: "audio/forest.mp3", volume: 1.0, loop: true, tags: { location: "forest" } },
      ];
      const result = selectTrackByLocation(tracks, "forest");
      expect(result?.id).toBe("forest");
    });

    it("exports getDefaultTrack", () => {
      const tracks: readonly AudioTrack[] = [
        { id: "default", path: "audio/default.mp3", volume: 1.0, loop: true, tags: {} },
      ];
      const result = getDefaultTrack(tracks);
      expect(result?.id).toBe("default");
    });

    it("exports createAudioPlayer", () => {
      const deps: AudioPlayerDeps = {
        context: createTestContext(),
        fetchFn: createTestFetch(),
        masterVolume: 1.0,
      };
      const player: AudioPlayer = createAudioPlayer(deps);
      expect(player.getState().isPlaying).toBe(false);
    });

    it("exports createBrowserAudioContext", () => {
      expect(typeof createBrowserAudioContext).toBe("function");
    });

    it("exports createDefaultAudioDependencies", () => {
      expect(typeof createDefaultAudioDependencies).toBe("function");
    });

    it("exports setupAudioStart", () => {
      expect(typeof setupAudioStart).toBe("function");
    });

    it("exports switchToNextTrack", () => {
      expect(typeof switchToNextTrack).toBe("function");
    });

    it("exports setupTrackSwitcher", () => {
      expect(typeof setupTrackSwitcher).toBe("function");
    });

    it("exports initializeAudio", () => {
      expect(typeof initializeAudio).toBe("function");
    });
  });

  describe("controller type exports", () => {
    it("exports AudioDependencies type", () => {
      const context = createTestContext();
      const deps: AudioDependencies = {
        createContext: (): AudioContextLike => context,
        fetchFn: createTestFetch(),
        addEventListenerFn: (): void => { /* no-op */ },
        removeEventListenerFn: (): void => { /* no-op */ },
      };
      expect(typeof deps.createContext).toBe("function");
    });

    it("exports AudioSystem type", () => {
      const context = createTestContext();
      const system: AudioSystem = {
        context,
        player: {
          play: (): void => { /* no-op */ },
          pause: (): void => { /* no-op */ },
          resume: (): void => { /* no-op */ },
          setVolume: (): void => { /* no-op */ },
          getState: (): { currentTrackId: string | null; isPlaying: boolean; volume: number } => ({
            currentTrackId: null, isPlaying: false, volume: 1,
          }),
        },
        tracks: [],
        currentIndex: 0,
        cleanup: (): void => { /* no-op */ },
      };
      expect(system.currentIndex).toBe(0);
    });
  });
});
