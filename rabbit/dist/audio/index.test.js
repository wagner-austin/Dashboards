/**
 * Tests for audio module public API exports.
 * Uses real test implementations instead of mocks.
 */
import { describe, it, expect } from "vitest";
import { createAudioState, validateAudioConfig, selectTrackByTime, selectTrackByLocation, getDefaultTrack, createAudioPlayer, createBrowserAudioContext, createDefaultAudioDependencies, switchToNextTrack, setupTrackSwitcher, initializeAudio, } from "./index.js";
/** Create test AudioParam. */
function createTestAudioParam() {
    const ramps = [];
    return {
        value: 0,
        linearRampToValueAtTime(value, endTime) {
            ramps.push({ value, endTime });
        },
        get ramps() {
            return ramps;
        },
    };
}
/** Create test GainNode. */
function createTestGainNode() {
    const connections = [];
    const gain = createTestAudioParam();
    return {
        gain,
        connect(destination) {
            connections.push(destination);
        },
        get connections() {
            return connections;
        },
    };
}
/** Create test BufferSourceNode. */
function createTestBufferSource() {
    let started = false;
    let stopped = false;
    const connectedTo = [];
    return {
        buffer: null,
        loop: false,
        onended: null,
        connect(destination) {
            connectedTo.push(destination);
        },
        start() {
            started = true;
        },
        stop() {
            stopped = true;
        },
        get started() {
            return started;
        },
        get stopped() {
            return stopped;
        },
        get connectedTo() {
            return connectedTo;
        },
    };
}
/** Create test AudioContext. */
function createTestContext() {
    const sources = [];
    const gains = [];
    const destination = {};
    return {
        state: "running",
        destination,
        resume() {
            return Promise.resolve();
        },
        createBuffer() {
            return {};
        },
        createBufferSource() {
            const source = createTestBufferSource();
            sources.push(source);
            return source;
        },
        createGain() {
            const gain = createTestGainNode();
            gains.push(gain);
            return gain;
        },
        decodeAudioData() {
            return Promise.resolve({});
        },
        get sources() {
            return sources;
        },
        get gains() {
            return gains;
        },
    };
}
/** Create test fetch function. */
function createTestFetch() {
    return (url) => {
        void url;
        return Promise.resolve({
            ok: true,
            arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
        });
    };
}
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
        it("exports AudioContextLike type", () => {
            const context = createTestContext();
            expect(context.state).toBe("running");
        });
        it("exports AudioPlayerDeps type", () => {
            const deps = {
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
                context: createTestContext(),
                fetchFn: createTestFetch(),
                masterVolume: 1.0,
            };
            const player = createAudioPlayer(deps);
            expect(player.getState().isPlaying).toBe(false);
        });
        it("exports createBrowserAudioContext", () => {
            expect(typeof createBrowserAudioContext).toBe("function");
        });
        it("exports createDefaultAudioDependencies", () => {
            expect(typeof createDefaultAudioDependencies).toBe("function");
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
            const deps = {
                createContext: () => context,
                fetchFn: createTestFetch(),
                addEventListenerFn: () => { },
                removeEventListenerFn: () => { },
            };
            expect(typeof deps.createContext).toBe("function");
        });
        it("exports AudioSystem type", () => {
            const context = createTestContext();
            const system = {
                context,
                player: {
                    play: () => { },
                    pause: () => { },
                    resume: () => { },
                    setVolume: () => { },
                    getState: () => ({
                        currentTrackId: null, isPlaying: false, volume: 1,
                    }),
                },
                tracks: [],
                currentIndex: 0,
                cleanup: () => { },
            };
            expect(system.currentIndex).toBe(0);
        });
        it("exports DeferredAudioSystem type", () => {
            const deferred = {
                tracks: [],
                currentIndex: 0,
                cleanup: () => { },
                getSystem: () => null,
            };
            expect(deferred.currentIndex).toBe(0);
        });
    });
});
//# sourceMappingURL=index.test.js.map