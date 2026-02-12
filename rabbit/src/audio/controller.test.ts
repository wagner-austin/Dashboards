/**
 * @vitest-environment jsdom
 * Tests for audio controller.
 * Uses real test implementations instead of mocks.
 */

import { describe, it, expect } from "vitest";
import {
  switchToNextTrack,
  setupTrackSwitcher,
  initializeAudio,
  _test_hooks,
  type AudioDependencies,
  type AudioSystem,
} from "./controller.js";
import type { AudioTrack, AudioContextLike, AudioBufferSourceNodeLike, GainNodeLike, AudioParamLike } from "./types.js";

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
  readonly decodedBuffers: readonly ArrayBuffer[];
  readonly resumeCalled: boolean;
  readonly resumeRejects: boolean;
  setResumeRejects(value: boolean): void;
  setState(state: TestContextState): void;
}

/** Create test AudioContext. */
function createTestContext(initialState: TestContextState = "running"): TestContext {
  const sources: TestBufferSourceNode[] = [];
  const gains: TestGainNode[] = [];
  const decodedBuffers: ArrayBuffer[] = [];
  let resumeCalled = false;
  let resumeRejects = false;
  let currentState: TestContextState = initialState;
  const destination = {} as AudioNode;

  return {
    get state(): TestContextState {
      return currentState;
    },
    destination,
    resume(): Promise<void> {
      resumeCalled = true;
      if (resumeRejects) {
        return Promise.reject(new Error("Resume failed"));
      }
      return Promise.resolve();
    },
    createBuffer(): AudioBuffer {
      return {} as AudioBuffer;
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
    get resumeCalled(): boolean {
      return resumeCalled;
    },
    get resumeRejects(): boolean {
      return resumeRejects;
    },
    setResumeRejects(value: boolean): void {
      resumeRejects = value;
    },
    setState(state: TestContextState): void {
      currentState = state;
    },
  };
}

/** Create test fetch function. */
function createTestFetch(ok = true): (url: string) => Promise<Response> {
  return (_url: string): Promise<Response> => {
    return Promise.resolve({
      ok,
      arrayBuffer: (): Promise<ArrayBuffer> => Promise.resolve(new ArrayBuffer(8)),
    } as Response);
  };
}

/** Test audio deps with trackable event listeners. */
interface TestAudioDeps extends AudioDependencies {
  readonly handlers: ReadonlyMap<string, readonly (() => void)[]>;
  readonly context: TestContext;
  triggerEvent(type: string): void;
}

/** Create test audio dependencies with trackable event listeners. */
function createTestAudioDeps(contextState: TestContextState = "running"): TestAudioDeps {
  const handlers = new Map<string, (() => void)[]>();
  const context = createTestContext(contextState);
  const fetchFn = createTestFetch();
  return {
    createContext: (): AudioContextLike => context,
    fetchFn,
    addEventListenerFn: (type: string, handler: () => void): void => {
      const existing = handlers.get(type) ?? [];
      existing.push(handler);
      handlers.set(type, existing);
    },
    removeEventListenerFn: (type: string, handler: () => void): void => {
      const existing = handlers.get(type) ?? [];
      const idx = existing.indexOf(handler);
      if (idx >= 0) {
        existing.splice(idx, 1);
      }
    },
    triggerEvent(type: string): void {
      const list = handlers.get(type);
      if (list !== undefined && list.length > 0) {
        const handler = list[0];
        if (handler !== undefined) {
          handler();
        }
      }
    },
    get handlers(): ReadonlyMap<string, readonly (() => void)[]> {
      return handlers;
    },
    context,
  };
}

/** Create test player that tracks calls. */
interface TestPlayer {
  play(track: AudioTrack): void;
  pause(): void;
  resume(): void;
  setVolume(volume: number): void;
  getState(): { currentTrackId: string | null; isPlaying: boolean; volume: number };
  readonly playedTracks: readonly AudioTrack[];
}

/** Create test player. */
function createTestPlayer(): TestPlayer {
  const playedTracks: AudioTrack[] = [];
  let currentId: string | null = null;
  return {
    play(track: AudioTrack): void {
      playedTracks.push(track);
      currentId = track.id;
    },
    pause(): void { /* no-op */ },
    resume(): void { /* no-op */ },
    setVolume(): void { /* no-op */ },
    getState(): { currentTrackId: string | null; isPlaying: boolean; volume: number } {
      return { currentTrackId: currentId, isPlaying: false, volume: 1 };
    },
    get playedTracks(): readonly AudioTrack[] {
      return playedTracks;
    },
  };
}

/** Wait for async operations. */
async function flushPromises(): Promise<void> {
  await new Promise(resolve => setTimeout(resolve, 0));
}

describe("initializeAudio", () => {
  it("returns null when audio config is undefined", () => {
    const audioDeps = createTestAudioDeps();
    const result = initializeAudio(undefined, audioDeps);
    expect(result).toBe(null);
  });

  it("returns null when audio is disabled", () => {
    const audioDeps = createTestAudioDeps();
    const result = initializeAudio(
      { enabled: false, masterVolume: 0.5, tracks: [] },
      audioDeps
    );
    expect(result).toBe(null);
  });

  it("returns null when no tracks are configured", () => {
    const audioDeps = createTestAudioDeps();
    const result = initializeAudio(
      { enabled: true, masterVolume: 0.5, tracks: [] },
      audioDeps
    );
    expect(result).toBe(null);
  });

  it("returns deferred audio system when valid config provided", () => {
    const audioDeps = createTestAudioDeps();
    const result = initializeAudio(
      {
        enabled: true,
        masterVolume: 0.5,
        tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
      },
      audioDeps
    );

    expect(result).not.toBe(null);
    expect(result?.getSystem()).toBe(null);
    expect(typeof result?.cleanup).toBe("function");
  });

  it("registers event listeners for user interaction", () => {
    const audioDeps = createTestAudioDeps();
    initializeAudio(
      {
        enabled: true,
        masterVolume: 0.5,
        tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
      },
      audioDeps
    );

    expect(audioDeps.handlers.get("click")?.length).toBe(1);
    expect(audioDeps.handlers.get("touchstart")?.length).toBe(1);
    expect(audioDeps.handlers.get("touchend")?.length).toBe(1);
    expect(audioDeps.handlers.get("keydown")?.length).toBe(1);
  });

  it("creates audio system on first user interaction", () => {
    const audioDeps = createTestAudioDeps();
    const result = initializeAudio(
      {
        enabled: true,
        masterVolume: 0.5,
        tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
      },
      audioDeps
    );

    expect(result?.getSystem()).toBe(null);

    audioDeps.triggerEvent("click");

    const system = result?.getSystem();
    expect(system).not.toBe(null);
    expect(system?.context).toBeDefined();
    expect(system?.player).toBeDefined();
  });

  it("removes event listeners after user interaction", () => {
    const audioDeps = createTestAudioDeps();
    initializeAudio(
      {
        enabled: true,
        masterVolume: 0.5,
        tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
      },
      audioDeps
    );

    audioDeps.triggerEvent("click");

    expect(audioDeps.handlers.get("click")?.length).toBe(0);
    expect(audioDeps.handlers.get("touchstart")?.length).toBe(0);
    expect(audioDeps.handlers.get("touchend")?.length).toBe(0);
    expect(audioDeps.handlers.get("keydown")?.length).toBe(0);
  });

  it("only creates system once even with multiple calls", () => {
    const handlers = new Map<string, (() => void)[]>();
    const context = createTestContext();
    const fetchFn = createTestFetch();
    const capturedHandlers: (() => void)[] = [];

    const audioDeps: AudioDependencies = {
      createContext: (): AudioContextLike => context,
      fetchFn,
      addEventListenerFn: (type: string, handler: () => void): void => {
        const existing = handlers.get(type) ?? [];
        existing.push(handler);
        handlers.set(type, existing);
        if (type === "click") {
          capturedHandlers.push(handler);
        }
      },
      removeEventListenerFn: (type: string, handler: () => void): void => {
        const existing = handlers.get(type) ?? [];
        const idx = existing.indexOf(handler);
        if (idx >= 0) {
          existing.splice(idx, 1);
        }
      },
    };

    const result = initializeAudio(
      {
        enabled: true,
        masterVolume: 0.5,
        tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
      },
      audioDeps
    );

    const handler = capturedHandlers[0];
    expect(handler).toBeDefined();
    if (handler === undefined) return;

    handler();
    const system1 = result?.getSystem();

    handler();
    const system2 = result?.getSystem();

    expect(system1).toBe(system2);
  });

  it("plays track on suspended context without calling resume", async () => {
    const audioDeps = createTestAudioDeps("suspended");
    initializeAudio(
      {
        enabled: true,
        masterVolume: 0.5,
        tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
      },
      audioDeps
    );

    audioDeps.triggerEvent("click");
    await flushPromises();

    // We no longer call resume - just play directly
    expect(audioDeps.context.sources.length).toBeGreaterThan(0);
  });

  it("returns tracks and currentIndex starting at 0", () => {
    const audioDeps = createTestAudioDeps();
    const tracks = [
      { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
      { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
    ];
    const result = initializeAudio(
      { enabled: true, masterVolume: 0.5, tracks },
      audioDeps
    );

    expect(result).not.toBe(null);
    expect(result?.tracks).toBe(tracks);
    expect(result?.currentIndex).toBe(0);
  });

  it("cleanup removes all event listeners", () => {
    const audioDeps = createTestAudioDeps();
    const result = initializeAudio(
      {
        enabled: true,
        masterVolume: 0.5,
        tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
      },
      audioDeps
    );

    expect(audioDeps.handlers.get("click")?.length).toBe(1);

    result?.cleanup();

    expect(audioDeps.handlers.get("click")?.length).toBe(0);
    expect(audioDeps.handlers.get("touchstart")?.length).toBe(0);
    expect(audioDeps.handlers.get("touchend")?.length).toBe(0);
    expect(audioDeps.handlers.get("keydown")?.length).toBe(0);
  });

  it("system cleanup removes all event listeners", () => {
    const handlers = new Map<string, (() => void)[]>();
    const context = createTestContext();
    const fetchFn = createTestFetch();

    const audioDeps: AudioDependencies = {
      createContext: (): AudioContextLike => context,
      fetchFn,
      addEventListenerFn: (type: string, handler: () => void): void => {
        const existing = handlers.get(type) ?? [];
        existing.push(handler);
        handlers.set(type, existing);
      },
      removeEventListenerFn: (type: string, handler: () => void): void => {
        const existing = handlers.get(type) ?? [];
        const idx = existing.indexOf(handler);
        if (idx >= 0) {
          existing.splice(idx, 1);
        }
      },
    };

    const result = initializeAudio(
      {
        enabled: true,
        masterVolume: 0.5,
        tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
      },
      audioDeps
    );

    const clickHandler = handlers.get("click")?.[0];
    expect(clickHandler).toBeDefined();
    if (clickHandler === undefined) return;

    clickHandler();

    const system = result?.getSystem();
    expect(system).not.toBe(null);
    if (system === null || system === undefined) return;

    handlers.set("click", [clickHandler]);
    handlers.set("touchstart", [clickHandler]);
    handlers.set("touchend", [clickHandler]);
    handlers.set("keydown", [clickHandler]);

    system.cleanup();

    expect(handlers.get("click")?.length).toBe(0);
    expect(handlers.get("touchstart")?.length).toBe(0);
    expect(handlers.get("touchend")?.length).toBe(0);
    expect(handlers.get("keydown")?.length).toBe(0);
  });
});

describe("switchToNextTrack", () => {
  it("cycles through tracks", () => {
    const player = createTestPlayer();
    const tracks = [
      { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
      { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
    ];
    const audio: AudioSystem = {
      context: createTestContext(),
      player,
      tracks,
      currentIndex: 0,
      cleanup: (): void => { /* no-op */ },
    };

    switchToNextTrack(audio);
    expect(audio.currentIndex).toBe(1);
    expect(player.getState().currentTrackId).toBe("track2");

    switchToNextTrack(audio);
    expect(audio.currentIndex).toBe(0);
    expect(player.getState().currentTrackId).toBe("track1");
  });

  it("does nothing with single track", () => {
    const player = createTestPlayer();
    const tracks = [{ id: "only", path: "audio/only.mp3", volume: 1.0, loop: true, tags: {} }];
    const audio: AudioSystem = {
      context: createTestContext(),
      player,
      tracks,
      currentIndex: 0,
      cleanup: (): void => { /* no-op */ },
    };

    switchToNextTrack(audio);
    expect(audio.currentIndex).toBe(0);
  });

  it("handles undefined track at index gracefully", () => {
    const player = createTestPlayer();
    const audio: AudioSystem = {
      context: createTestContext(),
      player,
      tracks: [undefined, undefined] as unknown as readonly AudioTrack[],
      currentIndex: 0,
      cleanup: (): void => { /* no-op */ },
    };

    switchToNextTrack(audio);
    expect(audio.currentIndex).toBe(0);
  });
});

describe("setupTrackSwitcher", () => {
  it("responds to N key when system is initialized", () => {
    const player = createTestPlayer();
    const tracks = [
      { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
      { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
    ];
    const audio: AudioSystem = {
      context: createTestContext(),
      player,
      tracks,
      currentIndex: 0,
      cleanup: (): void => { /* no-op */ },
    };

    const handlers: ((e: Event) => void)[] = [];
    const addListenerFn = (_type: string, handler: (e: Event) => void): void => {
      handlers.push(handler);
    };

    setupTrackSwitcher(() => audio, addListenerFn);
    expect(handlers.length).toBe(1);
    const handler = handlers[0];
    expect(handler).toBeDefined();
    if (handler === undefined) return;

    handler(new KeyboardEvent("keydown", { key: "n" }));
    expect(audio.currentIndex).toBe(1);
  });

  it("responds to uppercase N key", () => {
    const player = createTestPlayer();
    const tracks = [
      { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
      { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
    ];
    const audio: AudioSystem = {
      context: createTestContext(),
      player,
      tracks,
      currentIndex: 0,
      cleanup: (): void => { /* no-op */ },
    };

    const handlers: ((e: Event) => void)[] = [];
    setupTrackSwitcher(() => audio, (_type, handler) => handlers.push(handler));
    const handler = handlers[0];
    if (handler === undefined) return;

    handler(new KeyboardEvent("keydown", { key: "N" }));
    expect(audio.currentIndex).toBe(1);
  });

  it("does nothing when system is null", () => {
    const handlers: ((e: Event) => void)[] = [];
    setupTrackSwitcher(() => null, (_type, handler) => handlers.push(handler));
    const handler = handlers[0];
    if (handler === undefined) return;

    handler(new KeyboardEvent("keydown", { key: "n" }));
  });

  it("ignores other keys", () => {
    const player = createTestPlayer();
    const tracks = [
      { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
      { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
    ];
    const audio: AudioSystem = {
      context: createTestContext(),
      player,
      tracks,
      currentIndex: 0,
      cleanup: (): void => { /* no-op */ },
    };

    const handlers: ((e: Event) => void)[] = [];
    setupTrackSwitcher(() => audio, (_type, handler) => handlers.push(handler));
    const handler = handlers[0];
    if (handler === undefined) return;

    handler(new KeyboardEvent("keydown", { key: "m" }));
    expect(audio.currentIndex).toBe(0);
  });

  it("ignores non-keyboard events", () => {
    const player = createTestPlayer();
    const tracks = [
      { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
      { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
    ];
    const audio: AudioSystem = {
      context: createTestContext(),
      player,
      tracks,
      currentIndex: 0,
      cleanup: (): void => { /* no-op */ },
    };

    const handlers: ((e: Event) => void)[] = [];
    setupTrackSwitcher(() => audio, (_type, handler) => handlers.push(handler));
    const handler = handlers[0];
    if (handler === undefined) return;

    handler(new MouseEvent("click"));
    expect(audio.currentIndex).toBe(0);
  });
});

describe("_test_hooks", () => {
  it("isKeyboardEvent returns true for KeyboardEvent", () => {
    const event = new KeyboardEvent("keydown", { key: "n" });
    expect(_test_hooks.isKeyboardEvent(event)).toBe(true);
  });

  it("isKeyboardEvent returns false for non-KeyboardEvent", () => {
    const event = new MouseEvent("click");
    expect(_test_hooks.isKeyboardEvent(event)).toBe(false);
  });

  it("getTrackAtIndex returns track at valid index", () => {
    const tracks = [
      { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
      { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
    ];
    expect(_test_hooks.getTrackAtIndex(tracks, 0)?.id).toBe("track1");
    expect(_test_hooks.getTrackAtIndex(tracks, 1)?.id).toBe("track2");
  });

  it("getTrackAtIndex returns undefined for invalid index", () => {
    const tracks = [{ id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} }];
    expect(_test_hooks.getTrackAtIndex(tracks, 5)).toBe(undefined);
    expect(_test_hooks.getTrackAtIndex(tracks, -1)).toBe(undefined);
  });

  it("exports all controller functions", () => {
    expect(_test_hooks.switchToNextTrack).toBe(switchToNextTrack);
    expect(_test_hooks.setupTrackSwitcher).toBe(setupTrackSwitcher);
    expect(_test_hooks.initializeAudio).toBe(initializeAudio);
  });
});
