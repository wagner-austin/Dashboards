/**
 * @vitest-environment jsdom
 * Tests for audio controller.
 * Uses real test implementations instead of mocks.
 */
import { describe, it, expect } from "vitest";
import { switchToNextTrack, setupTrackSwitcher, initializeAudio, _test_hooks, } from "./controller.js";
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
    return (_url) => {
        return Promise.resolve({
            ok,
            arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
        });
    };
}
/** Create test audio dependencies with trackable event listeners. */
function createTestAudioDeps(contextState = "running") {
    const handlers = new Map();
    const context = createTestContext(contextState);
    const fetchFn = createTestFetch();
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
        triggerEvent(type) {
            const list = handlers.get(type);
            if (list !== undefined && list.length > 0) {
                const handler = list[0];
                if (handler !== undefined) {
                    handler();
                }
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
    let currentId = null;
    return {
        play(track) {
            playedTracks.push(track);
            currentId = track.id;
        },
        pause() { },
        resume() { },
        setVolume() { },
        getState() {
            return { currentTrackId: currentId, isPlaying: false, volume: 1 };
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
    it("returns deferred audio system when valid config provided", () => {
        const audioDeps = createTestAudioDeps();
        const result = initializeAudio({
            enabled: true,
            masterVolume: 0.5,
            tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
        }, audioDeps);
        expect(result).not.toBe(null);
        expect(result?.getSystem()).toBe(null);
        expect(typeof result?.cleanup).toBe("function");
    });
    it("registers event listeners for user interaction", () => {
        const audioDeps = createTestAudioDeps();
        initializeAudio({
            enabled: true,
            masterVolume: 0.5,
            tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
        }, audioDeps);
        expect(audioDeps.handlers.get("click")?.length).toBe(1);
        expect(audioDeps.handlers.get("touchstart")?.length).toBe(1);
        expect(audioDeps.handlers.get("touchend")?.length).toBe(1);
        expect(audioDeps.handlers.get("keydown")?.length).toBe(1);
    });
    it("creates audio system on first user interaction", () => {
        const audioDeps = createTestAudioDeps();
        const result = initializeAudio({
            enabled: true,
            masterVolume: 0.5,
            tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
        }, audioDeps);
        expect(result?.getSystem()).toBe(null);
        audioDeps.triggerEvent("click");
        const system = result?.getSystem();
        expect(system).not.toBe(null);
        expect(system?.context).toBeDefined();
        expect(system?.player).toBeDefined();
    });
    it("removes event listeners after user interaction", () => {
        const audioDeps = createTestAudioDeps();
        initializeAudio({
            enabled: true,
            masterVolume: 0.5,
            tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
        }, audioDeps);
        audioDeps.triggerEvent("click");
        expect(audioDeps.handlers.get("click")?.length).toBe(0);
        expect(audioDeps.handlers.get("touchstart")?.length).toBe(0);
        expect(audioDeps.handlers.get("touchend")?.length).toBe(0);
        expect(audioDeps.handlers.get("keydown")?.length).toBe(0);
    });
    it("only creates system once even with multiple calls", () => {
        const handlers = new Map();
        const context = createTestContext();
        const fetchFn = createTestFetch();
        const capturedHandlers = [];
        const audioDeps = {
            createContext: () => context,
            fetchFn,
            addEventListenerFn: (type, handler) => {
                const existing = handlers.get(type) ?? [];
                existing.push(handler);
                handlers.set(type, existing);
                if (type === "click") {
                    capturedHandlers.push(handler);
                }
            },
            removeEventListenerFn: (type, handler) => {
                const existing = handlers.get(type) ?? [];
                const idx = existing.indexOf(handler);
                if (idx >= 0) {
                    existing.splice(idx, 1);
                }
            },
        };
        const result = initializeAudio({
            enabled: true,
            masterVolume: 0.5,
            tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
        }, audioDeps);
        const handler = capturedHandlers[0];
        expect(handler).toBeDefined();
        if (handler === undefined)
            return;
        handler();
        const system1 = result?.getSystem();
        handler();
        const system2 = result?.getSystem();
        expect(system1).toBe(system2);
    });
    it("resumes suspended context on interaction", async () => {
        const audioDeps = createTestAudioDeps("suspended");
        initializeAudio({
            enabled: true,
            masterVolume: 0.5,
            tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
        }, audioDeps);
        audioDeps.triggerEvent("click");
        await flushPromises();
        expect(audioDeps.context.resumeCalled).toBe(true);
    });
    it("plays track even when resume fails", async () => {
        const audioDeps = createTestAudioDeps("suspended");
        audioDeps.context.setResumeRejects(true);
        initializeAudio({
            enabled: true,
            masterVolume: 0.5,
            tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
        }, audioDeps);
        audioDeps.triggerEvent("click");
        await flushPromises();
        expect(audioDeps.context.resumeCalled).toBe(true);
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
    it("cleanup removes all event listeners", () => {
        const audioDeps = createTestAudioDeps();
        const result = initializeAudio({
            enabled: true,
            masterVolume: 0.5,
            tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
        }, audioDeps);
        expect(audioDeps.handlers.get("click")?.length).toBe(1);
        result?.cleanup();
        expect(audioDeps.handlers.get("click")?.length).toBe(0);
        expect(audioDeps.handlers.get("touchstart")?.length).toBe(0);
        expect(audioDeps.handlers.get("touchend")?.length).toBe(0);
        expect(audioDeps.handlers.get("keydown")?.length).toBe(0);
    });
    it("system cleanup removes all event listeners", () => {
        const handlers = new Map();
        const context = createTestContext();
        const fetchFn = createTestFetch();
        const audioDeps = {
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
        };
        const result = initializeAudio({
            enabled: true,
            masterVolume: 0.5,
            tracks: [{ id: "test", path: "audio/test.mp3", volume: 1.0, loop: true, tags: {} }],
        }, audioDeps);
        const clickHandler = handlers.get("click")?.[0];
        expect(clickHandler).toBeDefined();
        if (clickHandler === undefined)
            return;
        clickHandler();
        const system = result?.getSystem();
        expect(system).not.toBe(null);
        if (system === null || system === undefined)
            return;
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
        const audio = {
            context: createTestContext(),
            player,
            tracks,
            currentIndex: 0,
            cleanup: () => { },
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
        const audio = {
            context: createTestContext(),
            player,
            tracks,
            currentIndex: 0,
            cleanup: () => { },
        };
        switchToNextTrack(audio);
        expect(audio.currentIndex).toBe(0);
    });
    it("handles undefined track at index gracefully", () => {
        const player = createTestPlayer();
        const audio = {
            context: createTestContext(),
            player,
            tracks: [undefined, undefined],
            currentIndex: 0,
            cleanup: () => { },
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
        const audio = {
            context: createTestContext(),
            player,
            tracks,
            currentIndex: 0,
            cleanup: () => { },
        };
        const handlers = [];
        const addListenerFn = (_type, handler) => {
            handlers.push(handler);
        };
        setupTrackSwitcher(() => audio, addListenerFn);
        expect(handlers.length).toBe(1);
        const handler = handlers[0];
        expect(handler).toBeDefined();
        if (handler === undefined)
            return;
        handler(new KeyboardEvent("keydown", { key: "n" }));
        expect(audio.currentIndex).toBe(1);
    });
    it("responds to uppercase N key", () => {
        const player = createTestPlayer();
        const tracks = [
            { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
            { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
        ];
        const audio = {
            context: createTestContext(),
            player,
            tracks,
            currentIndex: 0,
            cleanup: () => { },
        };
        const handlers = [];
        setupTrackSwitcher(() => audio, (_type, handler) => handlers.push(handler));
        const handler = handlers[0];
        if (handler === undefined)
            return;
        handler(new KeyboardEvent("keydown", { key: "N" }));
        expect(audio.currentIndex).toBe(1);
    });
    it("does nothing when system is null", () => {
        const handlers = [];
        setupTrackSwitcher(() => null, (_type, handler) => handlers.push(handler));
        const handler = handlers[0];
        if (handler === undefined)
            return;
        handler(new KeyboardEvent("keydown", { key: "n" }));
    });
    it("ignores other keys", () => {
        const player = createTestPlayer();
        const tracks = [
            { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
            { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
        ];
        const audio = {
            context: createTestContext(),
            player,
            tracks,
            currentIndex: 0,
            cleanup: () => { },
        };
        const handlers = [];
        setupTrackSwitcher(() => audio, (_type, handler) => handlers.push(handler));
        const handler = handlers[0];
        if (handler === undefined)
            return;
        handler(new KeyboardEvent("keydown", { key: "m" }));
        expect(audio.currentIndex).toBe(0);
    });
    it("ignores non-keyboard events", () => {
        const player = createTestPlayer();
        const tracks = [
            { id: "track1", path: "audio/track1.mp3", volume: 1.0, loop: true, tags: {} },
            { id: "track2", path: "audio/track2.mp3", volume: 1.0, loop: true, tags: {} },
        ];
        const audio = {
            context: createTestContext(),
            player,
            tracks,
            currentIndex: 0,
            cleanup: () => { },
        };
        const handlers = [];
        setupTrackSwitcher(() => audio, (_type, handler) => handlers.push(handler));
        const handler = handlers[0];
        if (handler === undefined)
            return;
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
//# sourceMappingURL=controller.test.js.map