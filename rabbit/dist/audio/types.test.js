/**
 * Tests for audio type definitions.
 */
import { describe, it, expect } from "vitest";
import { createAudioState, _test_hooks } from "./types.js";
describe("createAudioState", () => {
    it("returns initial state with null track", () => {
        const state = createAudioState();
        expect(state.currentTrackId).toBe(null);
    });
    it("returns initial state with isPlaying false", () => {
        const state = createAudioState();
        expect(state.isPlaying).toBe(false);
    });
    it("returns initial state with volume 1.0", () => {
        const state = createAudioState();
        expect(state.volume).toBe(1.0);
    });
    it("is exported via _test_hooks", () => {
        expect(_test_hooks.createAudioState).toBe(createAudioState);
    });
});
describe("type definitions", () => {
    it("AudioTrack has required fields", () => {
        const track = {
            id: "test",
            path: "audio/test.mp3",
            volume: 0.8,
            loop: true,
            tags: {},
        };
        expect(track.id).toBe("test");
        expect(track.path).toBe("audio/test.mp3");
        expect(track.volume).toBe(0.8);
        expect(track.loop).toBe(true);
        expect(track.tags).toEqual({});
    });
    it("TrackTags can have time tag", () => {
        const tags = { time: "day" };
        expect(tags.time).toBe("day");
        expect(tags.location).toBeUndefined();
    });
    it("TrackTags can have location tag", () => {
        const tags = { location: "forest" };
        expect(tags.location).toBe("forest");
        expect(tags.time).toBeUndefined();
    });
    it("TrackTags can have both tags", () => {
        const tags = { time: "night", location: "cave" };
        expect(tags.time).toBe("night");
        expect(tags.location).toBe("cave");
    });
    it("TimeOfDay includes all time values", () => {
        const times = ["day", "night", "dawn", "dusk"];
        expect(times).toHaveLength(4);
        expect(times).toContain("day");
        expect(times).toContain("night");
        expect(times).toContain("dawn");
        expect(times).toContain("dusk");
    });
    it("AudioConfig has required fields", () => {
        const config = {
            enabled: true,
            masterVolume: 0.5,
            tracks: [],
        };
        expect(config.enabled).toBe(true);
        expect(config.masterVolume).toBe(0.5);
        expect(config.tracks).toEqual([]);
    });
    it("AudioState has required fields", () => {
        const state = {
            currentTrackId: "test",
            isPlaying: true,
            volume: 0.7,
        };
        expect(state.currentTrackId).toBe("test");
        expect(state.isPlaying).toBe(true);
        expect(state.volume).toBe(0.7);
    });
});
//# sourceMappingURL=types.test.js.map