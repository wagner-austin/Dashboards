/**
 * Tests for track selection functions.
 */
import { describe, it, expect } from "vitest";
import { selectTrackByTime, selectTrackByLocation, getDefaultTrack, _test_hooks } from "./TrackSelector.js";
/** Create a test track with minimal required fields */
function createTestTrack(id, options) {
    return {
        id,
        path: `audio/${id}.mp3`,
        volume: 1.0,
        loop: true,
        tags: {
            ...(options?.time !== undefined ? { time: options.time } : {}),
            ...(options?.location !== undefined ? { location: options.location } : {}),
        },
    };
}
describe("selectTrackByTime", () => {
    it("returns matching track for day", () => {
        const tracks = [
            createTestTrack("day-music", { time: "day" }),
            createTestTrack("night-music", { time: "night" }),
        ];
        const result = selectTrackByTime(tracks, "day");
        expect(result?.id).toBe("day-music");
    });
    it("returns matching track for night", () => {
        const tracks = [
            createTestTrack("day-music", { time: "day" }),
            createTestTrack("night-music", { time: "night" }),
        ];
        const result = selectTrackByTime(tracks, "night");
        expect(result?.id).toBe("night-music");
    });
    it("returns matching track for dawn", () => {
        const tracks = [createTestTrack("dawn-music", { time: "dawn" })];
        const result = selectTrackByTime(tracks, "dawn");
        expect(result?.id).toBe("dawn-music");
    });
    it("returns matching track for dusk", () => {
        const tracks = [createTestTrack("dusk-music", { time: "dusk" })];
        const result = selectTrackByTime(tracks, "dusk");
        expect(result?.id).toBe("dusk-music");
    });
    it("returns first matching track when multiple match", () => {
        const tracks = [
            createTestTrack("day-1", { time: "day" }),
            createTestTrack("day-2", { time: "day" }),
        ];
        const result = selectTrackByTime(tracks, "day");
        expect(result?.id).toBe("day-1");
    });
    it("returns null when no matching track", () => {
        const tracks = [createTestTrack("day-music", { time: "day" })];
        const result = selectTrackByTime(tracks, "night");
        expect(result).toBe(null);
    });
    it("returns null for empty tracks array", () => {
        const result = selectTrackByTime([], "day");
        expect(result).toBe(null);
    });
    it("skips tracks without time tag", () => {
        const tracks = [
            createTestTrack("ambient"),
            createTestTrack("day-music", { time: "day" }),
        ];
        const result = selectTrackByTime(tracks, "day");
        expect(result?.id).toBe("day-music");
    });
});
describe("selectTrackByLocation", () => {
    it("returns matching track for location", () => {
        const tracks = [
            createTestTrack("forest-music", { location: "forest" }),
            createTestTrack("cave-music", { location: "cave" }),
        ];
        const result = selectTrackByLocation(tracks, "forest");
        expect(result?.id).toBe("forest-music");
    });
    it("returns first matching track when multiple match", () => {
        const tracks = [
            createTestTrack("forest-1", { location: "forest" }),
            createTestTrack("forest-2", { location: "forest" }),
        ];
        const result = selectTrackByLocation(tracks, "forest");
        expect(result?.id).toBe("forest-1");
    });
    it("returns null when no matching track", () => {
        const tracks = [createTestTrack("forest-music", { location: "forest" })];
        const result = selectTrackByLocation(tracks, "cave");
        expect(result).toBe(null);
    });
    it("returns null for empty tracks array", () => {
        const result = selectTrackByLocation([], "forest");
        expect(result).toBe(null);
    });
    it("skips tracks without location tag", () => {
        const tracks = [
            createTestTrack("ambient"),
            createTestTrack("forest-music", { location: "forest" }),
        ];
        const result = selectTrackByLocation(tracks, "forest");
        expect(result?.id).toBe("forest-music");
    });
});
describe("getDefaultTrack", () => {
    it("returns first track from array", () => {
        const tracks = [createTestTrack("first"), createTestTrack("second")];
        const result = getDefaultTrack(tracks);
        expect(result?.id).toBe("first");
    });
    it("returns null for empty array", () => {
        const result = getDefaultTrack([]);
        expect(result).toBe(null);
    });
    it("returns single track from single-element array", () => {
        const tracks = [createTestTrack("only")];
        const result = getDefaultTrack(tracks);
        expect(result?.id).toBe("only");
    });
});
describe("_test_hooks", () => {
    it("exports selectTrackByTime", () => {
        expect(_test_hooks.selectTrackByTime).toBe(selectTrackByTime);
    });
    it("exports selectTrackByLocation", () => {
        expect(_test_hooks.selectTrackByLocation).toBe(selectTrackByLocation);
    });
    it("exports getDefaultTrack", () => {
        expect(_test_hooks.getDefaultTrack).toBe(getDefaultTrack);
    });
});
//# sourceMappingURL=TrackSelector.test.js.map