/**
 * @vitest-environment jsdom
 * Tests for sprite loading and animation timer utilities.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createAnimationTimer, _test_hooks } from "./sprites.js";

const { isRecord, isStringArray, isSettings, validateSpriteModule, validateOptionalAudio, validateConfig } = _test_hooks;

describe("isRecord", () => {
  it("returns true for plain objects", () => {
    expect(isRecord({})).toBe(true);
    expect(isRecord({ key: "value" })).toBe(true);
  });

  it("returns false for null", () => {
    expect(isRecord(null)).toBe(false);
  });

  it("returns false for arrays", () => {
    expect(isRecord([])).toBe(false);
    expect(isRecord([1, 2, 3])).toBe(false);
  });

  it("returns false for primitives", () => {
    expect(isRecord("string")).toBe(false);
    expect(isRecord(123)).toBe(false);
    expect(isRecord(true)).toBe(false);
    expect(isRecord(undefined)).toBe(false);
  });
});

describe("isStringArray", () => {
  it("returns true for empty array", () => {
    expect(isStringArray([])).toBe(true);
  });

  it("returns true for string array", () => {
    expect(isStringArray(["a", "b", "c"])).toBe(true);
  });

  it("returns false for mixed array", () => {
    expect(isStringArray(["a", 1, "c"])).toBe(false);
  });

  it("returns false for non-arrays", () => {
    expect(isStringArray("string")).toBe(false);
    expect(isStringArray({})).toBe(false);
    expect(isStringArray(null)).toBe(false);
  });
});

describe("isSettings", () => {
  it("returns true for valid settings", () => {
    expect(isSettings({ fps: 60, jumpSpeed: 10, scrollSpeed: 100 })).toBe(true);
  });

  it("returns false for missing fps", () => {
    expect(isSettings({ jumpSpeed: 10, scrollSpeed: 100 })).toBe(false);
  });

  it("returns false for missing jumpSpeed", () => {
    expect(isSettings({ fps: 60, scrollSpeed: 100 })).toBe(false);
  });

  it("returns false for missing scrollSpeed", () => {
    expect(isSettings({ fps: 60, jumpSpeed: 10 })).toBe(false);
  });

  it("returns false for non-number values", () => {
    expect(isSettings({ fps: "60", jumpSpeed: 10, scrollSpeed: 100 })).toBe(false);
  });

  it("returns false for non-objects", () => {
    expect(isSettings(null)).toBe(false);
    expect(isSettings([])).toBe(false);
  });
});

describe("validateSpriteModule", () => {
  it("validates valid sprite module", () => {
    const module = { frames: ["frame1", "frame2"] };
    const result = validateSpriteModule(module, "test.js");
    expect(result.frames).toEqual(["frame1", "frame2"]);
  });

  it("throws for non-object", () => {
    expect(() => validateSpriteModule(null, "test.js")).toThrow(
      "Invalid sprite module at test.js: not an object"
    );
    expect(() => validateSpriteModule("string", "test.js")).toThrow(
      "Invalid sprite module at test.js: not an object"
    );
  });

  it("throws for missing frames", () => {
    expect(() => validateSpriteModule({}, "test.js")).toThrow(
      "Invalid sprite module at test.js: frames must be string array"
    );
  });

  it("throws for non-string frames", () => {
    expect(() => validateSpriteModule({ frames: [1, 2, 3] }, "test.js")).toThrow(
      "Invalid sprite module at test.js: frames must be string array"
    );
  });
});

describe("validateOptionalAudio", () => {
  it("returns undefined when audio is undefined", () => {
    const result = validateOptionalAudio(undefined);
    expect(result).toBeUndefined();
  });

  it("validates and returns audio config when present", () => {
    const audioConfig = {
      enabled: true,
      masterVolume: 0.5,
      tracks: [{ id: "ambient", path: "audio/ambient.mp3", volume: 1.0, loop: true, tags: {} }],
    };
    const result = validateOptionalAudio(audioConfig);
    expect(result?.enabled).toBe(true);
    expect(result?.masterVolume).toBe(0.5);
    expect(result?.tracks.length).toBe(1);
  });

  it("throws for invalid audio config", () => {
    expect(() => validateOptionalAudio({ enabled: "yes" })).toThrow('audio: "enabled" must be a boolean');
  });
});

describe("validateConfig", () => {
  it("validates valid config", () => {
    const config = {
      sprites: { bunny: {} },
      layers: [],
      settings: { fps: 60, jumpSpeed: 10, scrollSpeed: 100 },
    };
    const result = validateConfig(config);
    expect(result.settings.fps).toBe(60);
  });

  it("validates config with audio", () => {
    const config = {
      sprites: { bunny: {} },
      layers: [],
      settings: { fps: 60, jumpSpeed: 10, scrollSpeed: 100 },
      audio: {
        enabled: true,
        masterVolume: 0.5,
        tracks: [],
      },
    };
    const result = validateConfig(config);
    expect(result.audio?.enabled).toBe(true);
    expect(result.audio?.masterVolume).toBe(0.5);
  });

  it("validates config without audio", () => {
    const config = {
      sprites: { bunny: {} },
      layers: [],
      settings: { fps: 60, jumpSpeed: 10, scrollSpeed: 100 },
    };
    const result = validateConfig(config);
    expect(result.audio).toBeUndefined();
  });

  it("throws for non-object", () => {
    expect(() => validateConfig(null)).toThrow("Invalid config: not an object");
    expect(() => validateConfig("string")).toThrow("Invalid config: not an object");
  });

  it("throws for missing sprites", () => {
    expect(() =>
      validateConfig({
        layers: [],
        settings: { fps: 60, jumpSpeed: 10, scrollSpeed: 100 },
      })
    ).toThrow("Invalid config: missing sprites object");
  });

  it("throws for missing layers", () => {
    expect(() =>
      validateConfig({
        sprites: {},
        settings: { fps: 60, jumpSpeed: 10, scrollSpeed: 100 },
      })
    ).toThrow("Invalid config: missing layers array");
  });

  it("throws for missing settings", () => {
    expect(() =>
      validateConfig({
        sprites: {},
        layers: [],
      })
    ).toThrow("Invalid config: invalid settings object");
  });

  it("throws for invalid settings", () => {
    expect(() =>
      validateConfig({
        sprites: {},
        layers: [],
        settings: { fps: "60", jumpSpeed: 10, scrollSpeed: 100 },
      })
    ).toThrow("Invalid config: invalid settings object");
  });

  it("throws for invalid audio", () => {
    expect(() =>
      validateConfig({
        sprites: {},
        layers: [],
        settings: { fps: 60, jumpSpeed: 10, scrollSpeed: 100 },
        audio: { enabled: "yes" },
      })
    ).toThrow('audio: "enabled" must be a boolean');
  });
});

describe("createAnimationTimer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  function createCounter(): { count: number; increment: () => void } {
    const state = { count: 0 };
    return {
      get count(): number {
        return state.count;
      },
      increment: (): void => {
        state.count++;
      },
    };
  }

  it("does not run until started", () => {
    const counter = createCounter();
    createAnimationTimer(100, counter.increment);

    vi.advanceTimersByTime(500);
    expect(counter.count).toBe(0);
  });

  it("runs callback at specified interval after start", () => {
    const counter = createCounter();
    const timer = createAnimationTimer(100, counter.increment);

    timer.start();
    expect(counter.count).toBe(0);

    vi.advanceTimersByTime(100);
    expect(counter.count).toBe(1);

    vi.advanceTimersByTime(100);
    expect(counter.count).toBe(2);
  });

  it("stops running after stop", () => {
    const counter = createCounter();
    const timer = createAnimationTimer(100, counter.increment);

    timer.start();
    vi.advanceTimersByTime(100);
    expect(counter.count).toBe(1);

    timer.stop();
    vi.advanceTimersByTime(500);
    expect(counter.count).toBe(1);
  });

  it("can be restarted after stop", () => {
    const counter = createCounter();
    const timer = createAnimationTimer(100, counter.increment);

    timer.start();
    vi.advanceTimersByTime(100);
    timer.stop();

    timer.start();
    vi.advanceTimersByTime(100);
    expect(counter.count).toBe(2);
  });

  it("isRunning returns false initially", () => {
    const noop = (): void => { /* no-op */ };
    const timer = createAnimationTimer(100, noop);
    expect(timer.isRunning()).toBe(false);
  });

  it("isRunning returns true after start", () => {
    const noop = (): void => { /* no-op */ };
    const timer = createAnimationTimer(100, noop);
    timer.start();
    expect(timer.isRunning()).toBe(true);
  });

  it("isRunning returns false after stop", () => {
    const noop = (): void => { /* no-op */ };
    const timer = createAnimationTimer(100, noop);
    timer.start();
    timer.stop();
    expect(timer.isRunning()).toBe(false);
  });

  it("start is idempotent when already running", () => {
    const counter = createCounter();
    const timer = createAnimationTimer(100, counter.increment);

    timer.start();
    timer.start();
    timer.start();

    vi.advanceTimersByTime(100);
    expect(counter.count).toBe(1);
  });

  it("stop is idempotent when not running", () => {
    const noop = (): void => { /* no-op */ };
    const timer = createAnimationTimer(100, noop);

    // Should not throw
    timer.stop();
    timer.stop();
    timer.stop();
    expect(timer.isRunning()).toBe(false);
  });
});
