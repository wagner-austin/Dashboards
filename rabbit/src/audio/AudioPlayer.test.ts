/**
 * Tests for audio player.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createAudioPlayer, _test_hooks } from "./AudioPlayer.js";
import type { AudioElementLike, AudioPlayerDeps } from "./AudioPlayer.js";
import type { AudioTrack } from "./types.js";

/** Mock state for tracking element behavior */
interface MockElementState {
  playing: boolean;
  src: string;
  vol: number;
  looping: boolean;
}

/** Create a mock audio element with observable state */
function createMockElement(options?: { rejectPlay?: boolean }): AudioElementLike & { _state: MockElementState } {
  const mockState: MockElementState = { playing: false, src: "", vol: 1, looping: false };
  return {
    get src(): string {
      return mockState.src;
    },
    set src(s: string) {
      mockState.src = s;
    },
    get volume(): number {
      return mockState.vol;
    },
    set volume(v: number) {
      mockState.vol = v;
    },
    get loop(): boolean {
      return mockState.looping;
    },
    set loop(l: boolean) {
      mockState.looping = l;
    },
    play(): Promise<void> {
      if (options?.rejectPlay === true) {
        return Promise.reject(new Error("Autoplay blocked"));
      }
      mockState.playing = true;
      return Promise.resolve();
    },
    pause(): void {
      mockState.playing = false;
    },
    _state: mockState,
  };
}

/** Create test track with minimal fields */
function createTestTrack(id: string, options?: { volume?: number; loop?: boolean }): AudioTrack {
  return {
    id,
    path: `audio/${id}.mp3`,
    volume: options?.volume ?? 1.0,
    loop: options?.loop ?? true,
    tags: {},
  };
}

/** Create test dependencies with mock element */
function createTestDeps(masterVolume = 1.0): AudioPlayerDeps & { elements: (AudioElementLike & { _state: MockElementState })[] } {
  const elements: (AudioElementLike & { _state: MockElementState })[] = [];
  return {
    createElement: (): AudioElementLike => {
      const el = createMockElement();
      elements.push(el);
      return el;
    },
    masterVolume,
    elements,
  };
}

describe("createAudioPlayer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("initial state", () => {
    it("starts with no current track", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      expect(player.getState().currentTrackId).toBe(null);
    });

    it("starts with isPlaying false", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      expect(player.getState().isPlaying).toBe(false);
    });

    it("starts with master volume from deps", () => {
      const deps = createTestDeps(0.5);
      const player = createAudioPlayer(deps);
      expect(player.getState().volume).toBe(0.5);
    });
  });

  describe("play", () => {
    it("sets current track id", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);

      expect(player.getState().currentTrackId).toBe("ambient");
    });

    it("sets isPlaying to true", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);

      expect(player.getState().isPlaying).toBe(true);
    });

    it("configures element with track path", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);

      expect(deps.elements[0]?._state.src).toBe("audio/ambient.mp3");
    });

    it("configures element with track loop setting", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);

      player.play(createTestTrack("looping", { loop: true }));
      expect(deps.elements[0]?._state.looping).toBe(true);

      player.play(createTestTrack("oneshot", { loop: false }));
      expect(deps.elements[1]?._state.looping).toBe(false);
    });

    it("starts at zero volume for fade-in", () => {
      const deps = createTestDeps(0.5);
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient", { volume: 0.8 });

      player.play(track);

      // Volume starts at 0 for fade-in
      expect(deps.elements[0]?._state.vol).toBe(0);
    });

    it("fades in to target volume over time", async () => {
      const deps = createTestDeps(0.5);
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient", { volume: 0.8 });

      player.play(track);
      // Wait for play promise to resolve
      await vi.runAllTimersAsync();

      // After full fade (2000ms), should reach target: 0.5 * 0.8 = 0.4
      expect(deps.elements[0]?._state.vol).toBeCloseTo(0.4);
    });

    it("gradually increases volume during fade", async () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient", { volume: 1.0 });

      player.play(track);
      // Wait for play promise
      await Promise.resolve();

      // After partial fade (500ms = half of 1000ms)
      vi.advanceTimersByTime(500);
      const midVolume = deps.elements[0]?._state.vol ?? 0;
      expect(midVolume).toBeGreaterThan(0);
      expect(midVolume).toBeLessThan(1);

      // After full fade
      vi.advanceTimersByTime(500);
      expect(deps.elements[0]?._state.vol).toBeCloseTo(1.0);
    });

    it("calls play on element", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);

      expect(deps.elements[0]?._state.playing).toBe(true);
    });

    it("crossfades when playing new track while one is playing", async () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      // Start first track and let it fade in completely
      player.play(createTestTrack("first", { volume: 1.0 }));
      await vi.runAllTimersAsync();
      expect(deps.elements[0]?._state.vol).toBeCloseTo(1.0);
      expect(deps.elements[0]?._state.playing).toBe(true);

      // Play second track - should start crossfade
      player.play(createTestTrack("second", { volume: 1.0 }));
      await Promise.resolve(); // Wait for play promise

      // Both should be playing during crossfade
      expect(deps.elements[0]?._state.playing).toBe(true);
      expect(deps.elements[1]?._state.playing).toBe(true);

      // After crossfade completes, first should be paused
      await vi.runAllTimersAsync();
      expect(deps.elements[0]?._state.playing).toBe(false);
      expect(deps.elements[0]?._state.vol).toBe(0);
      expect(deps.elements[1]?._state.vol).toBeCloseTo(1.0);
    });

    it("fades out old track during crossfade", async () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      // Start first track and let it fade in completely
      player.play(createTestTrack("first", { volume: 1.0 }));
      await vi.runAllTimersAsync();
      const initialVolume = deps.elements[0]?._state.vol ?? 0;
      expect(initialVolume).toBeCloseTo(1.0);

      // Play second track
      player.play(createTestTrack("second", { volume: 1.0 }));
      await Promise.resolve();

      // After partial crossfade (500ms = half of 1000ms fade)
      vi.advanceTimersByTime(500);
      const midVolume = deps.elements[0]?._state.vol ?? 0;
      expect(midVolume).toBeLessThan(initialVolume);
      expect(midVolume).toBeGreaterThan(0);
    });

    it("stops fade-in on old track when crossfading mid-fade", async () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      // Start first track
      player.play(createTestTrack("first", { volume: 1.0 }));
      await Promise.resolve();

      // Partial fade-in
      vi.advanceTimersByTime(500);
      const midFadeVolume = deps.elements[0]?._state.vol ?? 0;
      expect(midFadeVolume).toBeGreaterThan(0);
      expect(midFadeVolume).toBeLessThan(1);

      // Play second track mid-fade - should stop fade-in and start fade-out
      player.play(createTestTrack("second", { volume: 1.0 }));
      await Promise.resolve();

      // First track should start fading out from current volume
      vi.advanceTimersByTime(1000);
      const fadeOutVolume = deps.elements[0]?._state.vol ?? 0;
      expect(fadeOutVolume).toBeLessThan(midFadeVolume);
    });

    it("handles autoplay being blocked gracefully", async () => {
      // Create deps that return a rejecting element
      const elements: (AudioElementLike & { _state: MockElementState })[] = [];
      const deps: AudioPlayerDeps & { elements: typeof elements } = {
        createElement: (): AudioElementLike => {
          const el = createMockElement({ rejectPlay: true });
          elements.push(el);
          return el;
        },
        masterVolume: 1.0,
        elements,
      };
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      // Play should not throw even when autoplay is blocked
      player.play(track);
      await Promise.resolve(); // Let promise rejection be handled

      // State should still show as playing (awaiting user interaction)
      expect(player.getState().isPlaying).toBe(true);
      expect(player.getState().currentTrackId).toBe("ambient");
    });
  });

  describe("pause", () => {
    it("sets isPlaying to false", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      player.pause();

      expect(player.getState().isPlaying).toBe(false);
    });

    it("pauses the element", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      player.pause();

      expect(deps.elements[0]?._state.playing).toBe(false);
    });

    it("does nothing if no element exists", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);

      // Should not throw
      player.pause();

      expect(player.getState().isPlaying).toBe(false);
    });

    it("preserves current track id", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      player.pause();

      expect(player.getState().currentTrackId).toBe("ambient");
    });

    it("stops fade-in when paused", async () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient", { volume: 1.0 });

      player.play(track);
      await Promise.resolve(); // Wait for play promise

      // Partial fade
      vi.advanceTimersByTime(500);
      const volumeBeforePause = deps.elements[0]?._state.vol ?? 0;

      player.pause();

      // Advance more time - volume should not change since fade stopped
      vi.advanceTimersByTime(1500);
      expect(deps.elements[0]?._state.vol).toBe(volumeBeforePause);
    });

    it("stops all fade-outs when paused", async () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      // Start first track and let it fade in
      player.play(createTestTrack("first", { volume: 1.0 }));
      await vi.runAllTimersAsync();
      expect(deps.elements[0]?._state.vol).toBeCloseTo(1.0);

      // Start crossfade to second track
      player.play(createTestTrack("second", { volume: 1.0 }));
      await Promise.resolve();
      vi.advanceTimersByTime(500);

      // First track should be fading out
      const midFadeVolume = deps.elements[0]?._state.vol ?? 0;
      expect(midFadeVolume).toBeLessThan(1.0);
      expect(midFadeVolume).toBeGreaterThan(0);

      // Pause - should stop all fades
      player.pause();
      const volumeAtPause = deps.elements[0]?._state.vol ?? 0;

      // Advance time - first track volume should not change
      vi.advanceTimersByTime(1500);
      expect(deps.elements[0]?._state.vol).toBe(volumeAtPause);
    });
  });

  describe("resume", () => {
    it("sets isPlaying to true", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      player.pause();
      player.resume();

      expect(player.getState().isPlaying).toBe(true);
    });

    it("calls play on element", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      player.pause();
      expect(deps.elements[0]?._state.playing).toBe(false);

      player.resume();
      expect(deps.elements[0]?._state.playing).toBe(true);
    });

    it("does nothing if no element exists", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);

      // Should not throw
      player.resume();

      expect(player.getState().isPlaying).toBe(false);
    });

    it("does nothing if already playing", () => {
      const deps = createTestDeps();
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      player.resume(); // Already playing

      expect(player.getState().isPlaying).toBe(true);
      // Only one element should be created
      expect(deps.elements.length).toBe(1);
    });

    it("handles play rejection gracefully on resume", async () => {
      // First create player with normal element, then make it reject on resume
      let shouldReject = false;
      const elements: (AudioElementLike & { _state: MockElementState })[] = [];
      const deps: AudioPlayerDeps & { elements: typeof elements } = {
        createElement: (): AudioElementLike => {
          const mockState: MockElementState = { playing: false, src: "", vol: 1, looping: false };
          const el: AudioElementLike & { _state: MockElementState } = {
            get src(): string { return mockState.src; },
            set src(s: string) { mockState.src = s; },
            get volume(): number { return mockState.vol; },
            set volume(v: number) { mockState.vol = v; },
            get loop(): boolean { return mockState.looping; },
            set loop(l: boolean) { mockState.looping = l; },
            play(): Promise<void> {
              if (shouldReject) {
                return Promise.reject(new Error("Not from user interaction"));
              }
              mockState.playing = true;
              return Promise.resolve();
            },
            pause(): void { mockState.playing = false; },
            _state: mockState,
          };
          elements.push(el);
          return el;
        },
        masterVolume: 1.0,
        elements,
      };
      const player = createAudioPlayer(deps);

      // Play and pause normally
      player.play(createTestTrack("ambient"));
      await Promise.resolve();
      player.pause();

      // Now make play reject
      shouldReject = true;

      // Resume should not throw even when play fails
      player.resume();
      await Promise.resolve(); // Let promise rejection be handled

      // State should show as playing (set before the promise)
      expect(player.getState().isPlaying).toBe(true);
    });
  });

  describe("setVolume", () => {
    it("updates volume state", () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      player.setVolume(0.7);

      expect(player.getState().volume).toBe(0.7);
    });

    it("clamps volume to minimum 0", () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      player.setVolume(-0.5);

      expect(player.getState().volume).toBe(0);
    });

    it("clamps volume to maximum 1", () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      player.setVolume(1.5);

      expect(player.getState().volume).toBe(1);
    });

    it("updates element volume when playing after fade completes", async () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient", { volume: 0.8 });

      player.play(track);
      await vi.runAllTimersAsync(); // Complete fade-in
      expect(deps.elements[0]?._state.vol).toBeCloseTo(0.8); // 1.0 * 0.8

      player.setVolume(0.5);
      expect(deps.elements[0]?._state.vol).toBeCloseTo(0.4); // 0.5 * 0.8
    });

    it("does nothing to element if not playing", () => {
      const deps = createTestDeps(1.0);
      const player = createAudioPlayer(deps);

      // Should not throw
      player.setVolume(0.5);

      expect(player.getState().volume).toBe(0.5);
    });
  });

  describe("getState", () => {
    it("returns immutable snapshot", () => {
      const deps = createTestDeps(0.5);
      const player = createAudioPlayer(deps);
      const track = createTestTrack("ambient");

      player.play(track);
      const state1 = player.getState();

      player.pause();
      const state2 = player.getState();

      // Original state should not be mutated
      expect(state1.isPlaying).toBe(true);
      expect(state2.isPlaying).toBe(false);
    });
  });
});

describe("_test_hooks", () => {
  it("exports createAudioPlayer", () => {
    expect(_test_hooks.createAudioPlayer).toBe(createAudioPlayer);
  });
});
