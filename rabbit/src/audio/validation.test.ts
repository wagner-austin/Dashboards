/**
 * Tests for audio validation functions.
 */

import { describe, it, expect } from "vitest";
import { validateAudioConfig, _test_hooks } from "./validation.js";

const { isRecord, isTimeOfDay, isTrackTags, requireAudioTrack } = _test_hooks;

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

describe("isTimeOfDay", () => {
  it("returns true for valid time values", () => {
    expect(isTimeOfDay("day")).toBe(true);
    expect(isTimeOfDay("night")).toBe(true);
    expect(isTimeOfDay("dawn")).toBe(true);
    expect(isTimeOfDay("dusk")).toBe(true);
  });

  it("returns false for invalid time values", () => {
    expect(isTimeOfDay("morning")).toBe(false);
    expect(isTimeOfDay("evening")).toBe(false);
    expect(isTimeOfDay("")).toBe(false);
    expect(isTimeOfDay(null)).toBe(false);
    expect(isTimeOfDay(123)).toBe(false);
  });
});

describe("isTrackTags", () => {
  it("returns true for empty tags", () => {
    expect(isTrackTags({})).toBe(true);
  });

  it("returns true for valid time tag", () => {
    expect(isTrackTags({ time: "day" })).toBe(true);
    expect(isTrackTags({ time: "night" })).toBe(true);
    expect(isTrackTags({ time: "dawn" })).toBe(true);
    expect(isTrackTags({ time: "dusk" })).toBe(true);
  });

  it("returns true for valid location tag", () => {
    expect(isTrackTags({ location: "forest" })).toBe(true);
    expect(isTrackTags({ location: "cave" })).toBe(true);
  });

  it("returns true for both tags", () => {
    expect(isTrackTags({ time: "day", location: "forest" })).toBe(true);
  });

  it("returns false for invalid time tag", () => {
    expect(isTrackTags({ time: "morning" })).toBe(false);
    expect(isTrackTags({ time: 123 })).toBe(false);
  });

  it("returns false for invalid location tag", () => {
    expect(isTrackTags({ location: 123 })).toBe(false);
    expect(isTrackTags({ location: null })).toBe(false);
  });

  it("returns false for non-objects", () => {
    expect(isTrackTags(null)).toBe(false);
    expect(isTrackTags("string")).toBe(false);
    expect(isTrackTags([])).toBe(false);
  });
});

describe("requireAudioTrack", () => {
  it("validates valid track with all fields", () => {
    const result = requireAudioTrack(
      { id: "test", path: "audio/test.mp3", volume: 0.8, loop: true, tags: {} },
      0
    );
    expect(result.id).toBe("test");
    expect(result.path).toBe("audio/test.mp3");
    expect(result.volume).toBe(0.8);
    expect(result.loop).toBe(true);
    expect(result.tags).toEqual({});
  });

  it("validates track with time tag", () => {
    const result = requireAudioTrack(
      { id: "day-music", path: "audio/day.mp3", volume: 1.0, loop: true, tags: { time: "day" } },
      0
    );
    expect(result.tags.time).toBe("day");
  });

  it("validates track with location tag", () => {
    const result = requireAudioTrack(
      { id: "forest-music", path: "audio/forest.mp3", volume: 0.5, loop: false, tags: { location: "forest" } },
      0
    );
    expect(result.tags.location).toBe("forest");
  });

  it("validates track with both tags", () => {
    const result = requireAudioTrack(
      { id: "combo", path: "audio/combo.mp3", volume: 0.7, loop: true, tags: { time: "night", location: "cave" } },
      0
    );
    expect(result.tags.time).toBe("night");
    expect(result.tags.location).toBe("cave");
  });

  it("throws for non-object", () => {
    expect(() => requireAudioTrack(null, 0)).toThrow("audio.tracks[0]: must be an object");
    expect(() => requireAudioTrack("string", 1)).toThrow("audio.tracks[1]: must be an object");
    expect(() => requireAudioTrack([], 2)).toThrow("audio.tracks[2]: must be an object");
  });

  it("throws for missing id", () => {
    expect(() => requireAudioTrack({}, 0)).toThrow('audio.tracks[0]: missing or invalid "id" field');
    expect(() => requireAudioTrack({ id: "" }, 0)).toThrow('audio.tracks[0]: missing or invalid "id" field');
    expect(() => requireAudioTrack({ id: 123 }, 0)).toThrow('audio.tracks[0]: missing or invalid "id" field');
  });

  it("throws for missing path", () => {
    expect(() => requireAudioTrack({ id: "test" }, 0)).toThrow(
      'audio.tracks[0] "test": missing or invalid "path" field'
    );
    expect(() => requireAudioTrack({ id: "test", path: "" }, 0)).toThrow(
      'audio.tracks[0] "test": missing or invalid "path" field'
    );
    expect(() => requireAudioTrack({ id: "test", path: 123 }, 0)).toThrow(
      'audio.tracks[0] "test": missing or invalid "path" field'
    );
  });

  it("throws for invalid volume", () => {
    expect(() => requireAudioTrack({ id: "test", path: "a.mp3" }, 0)).toThrow(
      'audio.tracks[0] "test": "volume" must be a number between 0 and 1'
    );
    expect(() => requireAudioTrack({ id: "test", path: "a.mp3", volume: "0.5" }, 0)).toThrow(
      'audio.tracks[0] "test": "volume" must be a number between 0 and 1'
    );
    expect(() => requireAudioTrack({ id: "test", path: "a.mp3", volume: -0.1 }, 0)).toThrow(
      'audio.tracks[0] "test": "volume" must be a number between 0 and 1'
    );
    expect(() => requireAudioTrack({ id: "test", path: "a.mp3", volume: 1.1 }, 0)).toThrow(
      'audio.tracks[0] "test": "volume" must be a number between 0 and 1'
    );
  });

  it("throws for invalid loop", () => {
    expect(() => requireAudioTrack({ id: "test", path: "a.mp3", volume: 0.5 }, 0)).toThrow(
      'audio.tracks[0] "test": "loop" must be a boolean'
    );
    expect(() => requireAudioTrack({ id: "test", path: "a.mp3", volume: 0.5, loop: "yes" }, 0)).toThrow(
      'audio.tracks[0] "test": "loop" must be a boolean'
    );
    expect(() => requireAudioTrack({ id: "test", path: "a.mp3", volume: 0.5, loop: 1 }, 0)).toThrow(
      'audio.tracks[0] "test": "loop" must be a boolean'
    );
  });

  it("throws for invalid tags", () => {
    expect(() => requireAudioTrack({ id: "test", path: "a.mp3", volume: 0.5, loop: true }, 0)).toThrow(
      'audio.tracks[0] "test": "tags" must be a valid TrackTags object'
    );
    expect(() => requireAudioTrack({ id: "test", path: "a.mp3", volume: 0.5, loop: true, tags: null }, 0)).toThrow(
      'audio.tracks[0] "test": "tags" must be a valid TrackTags object'
    );
    expect(() =>
      requireAudioTrack({ id: "test", path: "a.mp3", volume: 0.5, loop: true, tags: { time: "invalid" } }, 0)
    ).toThrow('audio.tracks[0] "test": "tags" must be a valid TrackTags object');
  });
});

describe("validateAudioConfig", () => {
  it("validates valid audio config", () => {
    const result = validateAudioConfig({
      enabled: true,
      masterVolume: 0.5,
      tracks: [{ id: "ambient", path: "audio/ambient.mp3", volume: 1.0, loop: true, tags: {} }],
    });

    expect(result.enabled).toBe(true);
    expect(result.masterVolume).toBe(0.5);
    expect(result.tracks.length).toBe(1);
    expect(result.tracks[0]?.id).toBe("ambient");
  });

  it("validates config with empty tracks array", () => {
    const result = validateAudioConfig({
      enabled: false,
      masterVolume: 0.0,
      tracks: [],
    });

    expect(result.enabled).toBe(false);
    expect(result.masterVolume).toBe(0.0);
    expect(result.tracks).toEqual([]);
  });

  it("validates config with multiple tracks", () => {
    const result = validateAudioConfig({
      enabled: true,
      masterVolume: 0.8,
      tracks: [
        { id: "day", path: "audio/day.mp3", volume: 0.7, loop: true, tags: { time: "day" } },
        { id: "night", path: "audio/night.mp3", volume: 0.5, loop: true, tags: { time: "night" } },
      ],
    });

    expect(result.tracks.length).toBe(2);
    expect(result.tracks[0]?.id).toBe("day");
    expect(result.tracks[1]?.id).toBe("night");
  });

  it("throws for non-object", () => {
    expect(() => validateAudioConfig(null)).toThrow("audio: must be an object");
    expect(() => validateAudioConfig("string")).toThrow("audio: must be an object");
    expect(() => validateAudioConfig([])).toThrow("audio: must be an object");
  });

  it("throws for invalid enabled", () => {
    expect(() => validateAudioConfig({})).toThrow('audio: "enabled" must be a boolean');
    expect(() => validateAudioConfig({ enabled: "yes" })).toThrow('audio: "enabled" must be a boolean');
    expect(() => validateAudioConfig({ enabled: 1 })).toThrow('audio: "enabled" must be a boolean');
  });

  it("throws for invalid masterVolume", () => {
    expect(() => validateAudioConfig({ enabled: true })).toThrow(
      'audio: "masterVolume" must be a number between 0 and 1'
    );
    expect(() => validateAudioConfig({ enabled: true, masterVolume: "0.5" })).toThrow(
      'audio: "masterVolume" must be a number between 0 and 1'
    );
    expect(() => validateAudioConfig({ enabled: true, masterVolume: -0.1 })).toThrow(
      'audio: "masterVolume" must be a number between 0 and 1'
    );
    expect(() => validateAudioConfig({ enabled: true, masterVolume: 1.1 })).toThrow(
      'audio: "masterVolume" must be a number between 0 and 1'
    );
  });

  it("throws for invalid tracks", () => {
    expect(() => validateAudioConfig({ enabled: true, masterVolume: 0.5 })).toThrow(
      'audio: "tracks" must be an array'
    );
    expect(() => validateAudioConfig({ enabled: true, masterVolume: 0.5, tracks: "not-array" })).toThrow(
      'audio: "tracks" must be an array'
    );
    expect(() => validateAudioConfig({ enabled: true, masterVolume: 0.5, tracks: {} })).toThrow(
      'audio: "tracks" must be an array'
    );
  });

  it("throws for duplicate track ids", () => {
    expect(() =>
      validateAudioConfig({
        enabled: true,
        masterVolume: 0.5,
        tracks: [
          { id: "test", path: "a.mp3", volume: 0.5, loop: true, tags: {} },
          { id: "test", path: "b.mp3", volume: 0.5, loop: true, tags: {} },
        ],
      })
    ).toThrow('audio.tracks[1]: duplicate track id "test"');
  });

  it("propagates validation errors from individual tracks", () => {
    expect(() =>
      validateAudioConfig({
        enabled: true,
        masterVolume: 0.5,
        tracks: [{ invalid: true }],
      })
    ).toThrow('audio.tracks[0]: missing or invalid "id" field');
  });
});
