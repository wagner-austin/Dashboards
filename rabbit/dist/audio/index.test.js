/**
 * Tests for audio module public API exports.
 */
import { describe, it, expect } from "vitest";
import { 
// Types - imported for type checking only
createAudioState, validateAudioConfig, selectTrackByTime, selectTrackByLocation, getDefaultTrack, createAudioPlayer, createBrowserAudioElement, createDefaultAudioDependencies, setupAudioStart, switchToNextTrack, setupTrackSwitcher, initializeAudio, } from "./index.js";
describe("audio module exports", () => {
    describe("type exports", () => {
        it("exports TimeOfDay type", () => {
            const time = "day";
            expect(time).toBe("day");
        });
        it("exports TrackTags type", () => {
            const tags = { time: "night", location: "forest" };
            expect(tags.time).toBe("night");
        });
        it("exports AudioTrack type", () => {
            const track = {
                id: "test",
                path: "audio/test.mp3",
                volume: 1.0,
                loop: true,
                tags: {},
            };
            expect(track.id).toBe("test");
        });
        it("exports AudioConfig type", () => {
            const config = {
                enabled: true,
                masterVolume: 0.5,
                tracks: [],
            };
            expect(config.enabled).toBe(true);
        });
        it("exports AudioState type", () => {
            const state = {
                currentTrackId: null,
                isPlaying: false,
                volume: 1.0,
            };
            expect(state.isPlaying).toBe(false);
        });
        it("exports AudioElementLike type", () => {
            const element = {
                src: "",
                volume: 1,
                loop: false,
                play: () => Promise.resolve(),
                pause: () => { },
            };
            expect(element.src).toBe("");
        });
        it("exports AudioPlayerDeps type", () => {
            const deps = {
                createElement: () => ({
                    src: "",
                    volume: 1,
                    loop: false,
                    play: () => Promise.resolve(),
                    pause: () => { },
                }),
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
            const tracks = [
                { id: "day", path: "audio/day.mp3", volume: 1.0, loop: true, tags: { time: "day" } },
            ];
            const result = selectTrackByTime(tracks, "day");
            expect(result?.id).toBe("day");
        });
        it("exports selectTrackByLocation", () => {
            const tracks = [
                { id: "forest", path: "audio/forest.mp3", volume: 1.0, loop: true, tags: { location: "forest" } },
            ];
            const result = selectTrackByLocation(tracks, "forest");
            expect(result?.id).toBe("forest");
        });
        it("exports getDefaultTrack", () => {
            const tracks = [
                { id: "default", path: "audio/default.mp3", volume: 1.0, loop: true, tags: {} },
            ];
            const result = getDefaultTrack(tracks);
            expect(result?.id).toBe("default");
        });
        it("exports createAudioPlayer", () => {
            const deps = {
                createElement: () => ({
                    src: "",
                    volume: 1,
                    loop: false,
                    play: () => Promise.resolve(),
                    pause: () => { },
                }),
                masterVolume: 1.0,
            };
            const player = createAudioPlayer(deps);
            expect(player.getState().isPlaying).toBe(false);
        });
        it("exports createBrowserAudioElement", () => {
            expect(typeof createBrowserAudioElement).toBe("function");
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
            const deps = {
                createElementFn: () => ({
                    src: "",
                    volume: 1,
                    loop: false,
                    play: () => Promise.resolve(),
                    pause: () => { },
                }),
                addEventListenerFn: () => { },
                removeEventListenerFn: () => { },
            };
            expect(typeof deps.createElementFn).toBe("function");
        });
        it("exports AudioSystem type", () => {
            const system = {
                player: {
                    play: () => { },
                    pause: () => { },
                    resume: () => { },
                    setVolume: () => { },
                    getState: () => ({ currentTrackId: null, isPlaying: false, volume: 1 }),
                },
                tracks: [],
                currentIndex: 0,
                cleanup: () => { },
            };
            expect(system.currentIndex).toBe(0);
        });
    });
});
//# sourceMappingURL=index.test.js.map