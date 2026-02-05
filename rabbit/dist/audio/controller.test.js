/**
 * @vitest-environment jsdom
 * Tests for audio controller.
 */
import { describe, it, expect } from "vitest";
import { setupAudioStart, switchToNextTrack, setupTrackSwitcher, initializeAudio, _test_hooks, } from "./controller.js";
/** Create test audio dependencies with trackable event listeners */
function createTestAudioDeps() {
    const handlers = new Map();
    return {
        createElementFn: () => ({
            src: "",
            volume: 1,
            loop: false,
            play: () => Promise.resolve(),
            pause: () => { },
        }),
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
        handlers,
    };
}
describe("setupAudioStart", () => {
    it("registers event listeners for click, touchstart, keydown", () => {
        const audioDeps = createTestAudioDeps();
        const mockPlayer = {
            play: () => { },
            pause: () => { },
            resume: () => { },
            setVolume: () => { },
            getState: () => ({
                currentTrackId: null, isPlaying: false, volume: 1,
            }),
        };
        const mockTrack = { id: "test", path: "audio/test.mp3", volume: 1, loop: true, tags: {} };
        setupAudioStart(mockPlayer, mockTrack, audioDeps);
        expect(audioDeps.handlers.get("click")?.length).toBe(1);
        expect(audioDeps.handlers.get("touchstart")?.length).toBe(1);
        expect(audioDeps.handlers.get("keydown")?.length).toBe(1);
    });
    it("removes listeners after play is triggered", () => {
        const audioDeps = createTestAudioDeps();
        let playCalled = false;
        const mockPlayer = {
            play: () => { playCalled = true; },
            pause: () => { },
            resume: () => { },
            setVolume: () => { },
            getState: () => ({
                currentTrackId: null, isPlaying: false, volume: 1,
            }),
        };
        const mockTrack = { id: "test", path: "audio/test.mp3", volume: 1, loop: true, tags: {} };
        setupAudioStart(mockPlayer, mockTrack, audioDeps);
        // Get the click handler
        const clickHandlers = audioDeps.handlers.get("click");
        expect(clickHandlers?.length).toBe(1);
        // Trigger click
        const clickHandler = clickHandlers?.[0];
        if (clickHandler !== undefined) {
            clickHandler();
        }
        expect(playCalled).toBe(true);
        // Handlers should be removed after play
        expect(audioDeps.handlers.get("click")?.length).toBe(0);
        expect(audioDeps.handlers.get("touchstart")?.length).toBe(0);
        expect(audioDeps.handlers.get("keydown")?.length).toBe(0);
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
        // Manually create invalid state to test defensive code path
        const invalidAudio = {
            ...result,
            tracks: [undefined, undefined],
        };
        // Should not throw and should not change index when track is undefined
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
        // Simulate N key press
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
        // Switch once to index 1
        handler(new KeyboardEvent("keydown", { key: "n" }));
        expect(result.currentIndex).toBe(1);
        // Simulate uppercase N - should wrap back to 0
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
        // Simulate different key
        const event = new KeyboardEvent("keydown", { key: "m" });
        handler(event);
        expect(result.currentIndex).toBe(0); // Should not change
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