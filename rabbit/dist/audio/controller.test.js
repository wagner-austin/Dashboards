/**
 * @vitest-environment jsdom
 * Tests for audio controller.
 * Uses real test implementations instead of mocks.
 */
import { describe, it, expect } from "vitest";
import { setupAudioStart, switchToNextTrack, setupTrackSwitcher, initializeAudio, _test_hooks, } from "./controller.js";
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
function createTestContext(initialState = "running") {
    const sources = [];
    const gains = [];
    const decodedBuffers = [];
    let resumeCalled = false;
    let resumeRejects = false;
    let currentState = initialState;
    const destination = {};
    return {
        get state() {
            return currentState;
        },
        destination,
        resume() {
            resumeCalled = true;
            if (resumeRejects) {
                return Promise.reject(new Error("Resume failed"));
            }
            return Promise.resolve();
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
        decodeAudioData(data) {
            decodedBuffers.push(data);
            return Promise.resolve({});
        },
        get sources() {
            return sources;
        },
        get gains() {
            return gains;
        },
        get decodedBuffers() {
            return decodedBuffers;
        },
        get resumeCalled() {
            return resumeCalled;
        },
        get resumeRejects() {
            return resumeRejects;
        },
        setResumeRejects(value) {
            resumeRejects = value;
        },
        setState(state) {
            currentState = state;
        },
    };
}
/** Create test fetch function. */
function createTestFetch(ok = true) {
    const fetchedUrls = [];
    const fetchFn = (url) => {
        fetchedUrls.push(url);
        return Promise.resolve({
            ok,
            arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
        });
    };
    return [fetchFn, { get fetchedUrls() { return fetchedUrls; } }];
}
/** Create test audio dependencies with trackable event listeners. */
function createTestAudioDeps(contextState = "running") {
    const handlers = new Map();
    const context = createTestContext(contextState);
    const [fetchFn] = createTestFetch();
    return {
        createContext: () => context,
        fetchFn,
        addEventListenerFn: (type, handler) => {
            const existing = handlers.get(type) ?? [];
            existing.push(handler);
            handlers.set(type, existing);
        },
        removeEventListenerFn: (type, handler) => {
            const existing = handlers.get(type) ?? [];
            const idx = existing.indexOf(handler);
            if (idx >= 0) {
                existing.splice(idx, 1);
            }
        },
        get handlers() {
            return handlers;
        },
        context,
    };
}
/** Create test player. */
function createTestPlayer() {
    const playedTracks = [];
    return {
        play(track) {
            playedTracks.push(track);
        },
        pause() { },
        resume() { },
        setVolume() { },
        getState() {
            return { currentTrackId: null, isPlaying: false, volume: 1 };
        },
        get playedTracks() {
            return playedTracks;
        },
    };
}
/** Wait for async operations. */
async function flushPromises() {
    await new Promise(resolve => setTimeout(resolve, 0));
}
describe("setupAudioStart", () => {
    it("registers event listeners for click, touchstart, keydown", () => {
        const audioDeps = createTestAudioDeps();
        const player = createTestPlayer();
        const track = { id: "test", path: "audio/test.mp3", volume: 1, loop: true, tags: {} };
        setupAudioStart(audioDeps.context, player, track, audioDeps);
        expect(audioDeps.handlers.get("click")?.length).toBe(1);
        expect(audioDeps.handlers.get("touchstart")?.length).toBe(1);
        expect(audioDeps.handlers.get("keydown")?.length).toBe(1);
    });
    it("removes listeners after play is triggered", () => {
        const audioDeps = createTestAudioDeps();
        const player = createTestPlayer();
        const track = { id: "test", path: "audio/test.mp3", volume: 1, loop: true, tags: {} };
        setupAudioStart(audioDeps.context, player, track, audioDeps);
        const clickHandlers = audioDeps.handlers.get("click");
        expect(clickHandlers?.length).toBe(1);
        const clickHandler = clickHandlers?.[0];
        if (clickHandler !== undefined) {
            clickHandler();
        }
        expect(player.playedTracks.length).toBe(1);
        expect(audioDeps.handlers.get("click")?.length).toBe(0);
        expect(audioDeps.handlers.get("touchstart")?.length).toBe(0);
        expect(audioDeps.handlers.get("keydown")?.length).toBe(0);
    });
    it("resumes suspended context before playing", async () => {
        const audioDeps = createTestAudioDeps("suspended");
        const player = createTestPlayer();
        const track = { id: "test", path: "audio/test.mp3", volume: 1, loop: true, tags: {} };
        setupAudioStart(audioDeps.context, player, track, audioDeps);
        const clickHandler = audioDeps.handlers.get("click")?.[0];
        if (clickHandler !== undefined) {
            clickHandler();
        }
        await flushPromises();
        expect(audioDeps.context.resumeCalled).toBe(true);
        expect(player.playedTracks.length).toBe(1);
    });
    it("handles resume failure gracefully", async () => {
        const audioDeps = createTestAudioDeps("suspended");
        audioDeps.context.setResumeRejects(true);
        const player = createTestPlayer();
        const track = { id: "test", path: "audio/test.mp3", volume: 1, loop: true, tags: {} };
        setupAudioStart(audioDeps.context, player, track, audioDeps);
        const clickHandler = audioDeps.handlers.get("click")?.[0];
        if (clickHandler !== undefined) {
            clickHandler();
        }
        await flushPromises();
        expect(audioDeps.context.resumeCalled).toBe(true);
        expect(player.playedTracks.length).toBe(0);
    });
});
describe("initializeAudio", () => {
    it("returns null when audio config is undefined", () => {
        const audioDeps = createTestAudioDeps();
        const result = initializeAudio(undefined, audioDeps);
        expect(result).toBe(null);
    });
    it("returns null when audio is disabled", () => {
        const audioDeps = createTestAudioDeps();
        const result = initializeAudio({ enabled: false, masterVolume: 0.5, tracks: [] }, audioDeps);
        expect(result).toBe(null);
    });
    it("returns null when no tracks are configured", () => {
        const audioDeps = createTestAudioDeps();
        const result = initializeAudio({ enabled: true, masterVolume: 0.5, tracks: [] }, audioDeps);
        expect(result).toBe(null);
    });
    it("returns audio system when valid config provided", () => {
        const audioDeps = createTestAudioDeps();
        const result = initializeAudio({
            enabled: true,
            masterVolume: 0.5,
            tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
        }, audioDeps);
        expect(result).not.toBe(null);
        expect(result?.player).toBeDefined();
        expect(result?.context).toBeDefined();
        expect(typeof result?.cleanup).toBe("function");
    });
    it("returns tracks and currentIndex starting at 0", () => {
        const audioDeps = createTestAudioDeps();
        const tracks = [
            { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
            { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
        ];
        const result = initializeAudio({ enabled: true, masterVolume: 0.5, tracks }, audioDeps);
        expect(result).not.toBe(null);
        expect(result?.tracks).toBe(tracks);
        expect(result?.currentIndex).toBe(0);
    });
});
describe("switchToNextTrack", () => {
    it("cycles through tracks", () => {
        const audioDeps = createTestAudioDeps();
        const tracks = [
            { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
            { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
        ];
        const result = initializeAudio({ enabled: true, masterVolume: 0.5, tracks }, audioDeps);
        expect(result).not.toBe(null);
        if (result === null)
            return;
        expect(result.currentIndex).toBe(0);
        switchToNextTrack(result);
        expect(result.currentIndex).toBe(1);
        expect(result.player.getState().currentTrackId).toBe("track2");
        switchToNextTrack(result);
        expect(result.currentIndex).toBe(0);
        expect(result.player.getState().currentTrackId).toBe("track1");
    });
    it("does nothing with single track", () => {
        const audioDeps = createTestAudioDeps();
        const tracks = [{ id: "only", path: "audio/only.mp3", volume: 1.0, loop: true, tags: {} }];
        const result = initializeAudio({ enabled: true, masterVolume: 0.5, tracks }, audioDeps);
        expect(result).not.toBe(null);
        if (result === null)
            return;
        switchToNextTrack(result);
        expect(result.currentIndex).toBe(0);
    });
    it("handles undefined track at index gracefully", () => {
        const audioDeps = createTestAudioDeps();
        const tracks = [
            { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
            { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
        ];
        const result = initializeAudio({ enabled: true, masterVolume: 0.5, tracks }, audioDeps);
        expect(result).not.toBe(null);
        if (result === null)
            return;
        const invalidAudio = {
            ...result,
            tracks: [undefined, undefined],
        };
        const originalIndex = invalidAudio.currentIndex;
        switchToNextTrack(invalidAudio);
        expect(invalidAudio.currentIndex).toBe(originalIndex);
    });
});
describe("setupTrackSwitcher", () => {
    it("responds to N key (lowercase)", () => {
        const audioDeps = createTestAudioDeps();
        const tracks = [
            { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
            { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
        ];
        const result = initializeAudio({ enabled: true, masterVolume: 0.5, tracks }, audioDeps);
        expect(result).not.toBe(null);
        if (result === null)
            return;
        const handlers = [];
        const addListenerFn = (_type, handler) => {
            handlers.push(handler);
        };
        setupTrackSwitcher(result, addListenerFn);
        expect(handlers.length).toBe(1);
        const handler = handlers[0];
        expect(handler).toBeDefined();
        if (handler === undefined)
            return;
        const event = new KeyboardEvent("keydown", { key: "n" });
        handler(event);
        expect(result.currentIndex).toBe(1);
    });
    it("responds to N key (uppercase)", () => {
        const audioDeps = createTestAudioDeps();
        const tracks = [
            { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
            { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
        ];
        const result = initializeAudio({ enabled: true, masterVolume: 0.5, tracks }, audioDeps);
        expect(result).not.toBe(null);
        if (result === null)
            return;
        const handlers = [];
        const addListenerFn = (_type, handler) => {
            handlers.push(handler);
        };
        setupTrackSwitcher(result, addListenerFn);
        const handler = handlers[0];
        if (handler === undefined)
            return;
        handler(new KeyboardEvent("keydown", { key: "n" }));
        expect(result.currentIndex).toBe(1);
        handler(new KeyboardEvent("keydown", { key: "N" }));
        expect(result.currentIndex).toBe(0);
    });
    it("ignores other keys", () => {
        const audioDeps = createTestAudioDeps();
        const tracks = [
            { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
            { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
        ];
        const result = initializeAudio({ enabled: true, masterVolume: 0.5, tracks }, audioDeps);
        expect(result).not.toBe(null);
        if (result === null)
            return;
        const handlers = [];
        const addListenerFn = (_type, handler) => {
            handlers.push(handler);
        };
        setupTrackSwitcher(result, addListenerFn);
        const handler = handlers[0];
        if (handler === undefined)
            return;
        const event = new KeyboardEvent("keydown", { key: "m" });
        handler(event);
        expect(result.currentIndex).toBe(0);
    });
    it("ignores non-keyboard events", () => {
        const audioDeps = createTestAudioDeps();
        const tracks = [
            { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
            { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
        ];
        const result = initializeAudio({ enabled: true, masterVolume: 0.5, tracks }, audioDeps);
        expect(result).not.toBe(null);
        if (result === null)
            return;
        const handlers = [];
        const addListenerFn = (_type, handler) => {
            handlers.push(handler);
        };
        setupTrackSwitcher(result, addListenerFn);
        const handler = handlers[0];
        if (handler === undefined)
            return;
        const event = new MouseEvent("click");
        handler(event);
        expect(result.currentIndex).toBe(0);
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
        expect(_test_hooks.setupAudioStart).toBe(setupAudioStart);
        expect(_test_hooks.switchToNextTrack).toBe(switchToNextTrack);
        expect(_test_hooks.setupTrackSwitcher).toBe(setupTrackSwitcher);
        expect(_test_hooks.initializeAudio).toBe(initializeAudio);
    });
});
//# sourceMappingURL=controller.test.js.map