/**
 * @vitest-environment jsdom
 * Tests for main entry point.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { init, _test_hooks } from "./main.js";
import { advanceAllSceneSpriteFrames, createLayerAnimationCallback } from "./entities/SceneSprite.js";
import { createSceneState } from "./layers/index.js";
import { LAYER_BEHAVIORS } from "./types.js";
import { createCamera } from "./world/Projection.js";
/** Test depth bounds (minZ=-110, maxZ=160, range=270) */
function createTestDepthBounds() {
    return { minZ: -110, maxZ: 160, range: 270 };
}
function createTestBunnyFrames() {
    return {
        walkLeft: ["walk_l_0", "walk_l_1"],
        walkRight: ["walk_r_0", "walk_r_1"],
        jumpLeft: ["jump_l_0"],
        jumpRight: ["jump_r_0"],
        idleLeft: ["idle_l_0"],
        idleRight: ["idle_r_0"],
        walkToIdleLeft: ["trans_l_0", "trans_l_1"],
        walkToIdleRight: ["trans_r_0", "trans_r_1"],
        walkToTurnAwayLeft: ["turn_away_l_0", "turn_away_l_1"],
        walkToTurnAwayRight: ["turn_away_r_0", "turn_away_r_1"],
        walkToTurnTowardLeft: ["turn_toward_l_0", "turn_toward_l_1"],
        walkToTurnTowardRight: ["turn_toward_r_0", "turn_toward_r_1"],
        hopAway: ["hop_away_0", "hop_away_1"],
        hopToward: ["hop_toward_0", "hop_toward_1"],
    };
}
function createTestConfig() {
    return {
        sprites: {},
        layers: [],
        settings: { fps: 60, jumpSpeed: 10, scrollSpeed: 100 },
        autoLayers: {
            sprites: ["tree1", "tree2"],
            minLayer: 8,
            maxLayer: 30,
            treesPerLayer: 2,
            seed: 42,
        },
    };
}
function createTestSpriteRegistry() {
    const sprites = new Map();
    // Provide minimal sprites for autoLayers (tree1, tree2)
    sprites.set("tree1", [{ width: 40, frames: ["tree1_frame"] }]);
    sprites.set("tree2", [{ width: 40, frames: ["tree2_frame"] }]);
    return { sprites };
}
function createTestLoadLayerSpritesFn() {
    return () => Promise.resolve(createTestSpriteRegistry());
}
/** Create test audio dependencies with no-op event listeners */
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
describe("init", () => {
    let screen;
    let rafCallbacks;
    beforeEach(() => {
        screen = document.createElement("pre");
        screen.id = "screen";
        document.body.appendChild(screen);
        rafCallbacks = [];
    });
    afterEach(() => {
        document.body.removeChild(screen);
    });
    it("throws when screen element not found", async () => {
        const deps = {
            getScreenElement: () => null,
            loadConfigFn: () => Promise.resolve(createTestConfig()),
            loadBunnyFramesFn: () => Promise.resolve(createTestBunnyFrames()),
            loadLayerSpritesFn: createTestLoadLayerSpritesFn(),
            requestAnimationFrameFn: () => 0,
            audioDeps: createTestAudioDeps(),
        };
        await expect(init(deps)).rejects.toThrow("Screen element not found");
    });
    it("throws when autoLayers not in config", async () => {
        const configWithoutAutoLayers = {
            sprites: {},
            layers: [],
            settings: { fps: 60, jumpSpeed: 10, scrollSpeed: 100 },
            // No autoLayers
        };
        const deps = {
            getScreenElement: () => screen,
            loadConfigFn: () => Promise.resolve(configWithoutAutoLayers),
            loadBunnyFramesFn: () => Promise.resolve(createTestBunnyFrames()),
            loadLayerSpritesFn: createTestLoadLayerSpritesFn(),
            requestAnimationFrameFn: () => 0,
            audioDeps: createTestAudioDeps(),
        };
        await expect(init(deps)).rejects.toThrow("config.autoLayers is required for depth movement");
    });
    it("initializes and starts render loop", async () => {
        const deps = {
            getScreenElement: () => screen,
            loadConfigFn: () => Promise.resolve(createTestConfig()),
            loadBunnyFramesFn: () => Promise.resolve(createTestBunnyFrames()),
            loadLayerSpritesFn: createTestLoadLayerSpritesFn(),
            requestAnimationFrameFn: (callback) => {
                rafCallbacks.push(callback);
                return rafCallbacks.length;
            },
            audioDeps: createTestAudioDeps(),
        };
        await init(deps);
        // Should have queued a render callback
        expect(rafCallbacks.length).toBe(1);
        // Simulate frame
        const firstCallback = rafCallbacks[0];
        if (firstCallback === undefined) {
            throw new Error("Expected callback to be defined");
        }
        firstCallback(1000);
        // Should have queued another callback
        expect(rafCallbacks.length).toBe(2);
    });
    it("handles resize event", async () => {
        const deps = {
            getScreenElement: () => screen,
            loadConfigFn: () => Promise.resolve(createTestConfig()),
            loadBunnyFramesFn: () => Promise.resolve(createTestBunnyFrames()),
            loadLayerSpritesFn: createTestLoadLayerSpritesFn(),
            requestAnimationFrameFn: () => 0,
            audioDeps: createTestAudioDeps(),
        };
        await init(deps);
        // Dispatch resize event - should not throw
        window.dispatchEvent(new Event("resize"));
    });
    it("initializes audio when config has audio enabled", async () => {
        const audioDeps = createTestAudioDeps();
        const configWithAudio = {
            ...createTestConfig(),
            audio: {
                enabled: true,
                masterVolume: 0.5,
                tracks: [{ id: "ambient", path: "audio/ambient.mp3", volume: 1.0, loop: true, tags: {} }],
            },
        };
        const deps = {
            getScreenElement: () => screen,
            loadConfigFn: () => Promise.resolve(configWithAudio),
            loadBunnyFramesFn: () => Promise.resolve(createTestBunnyFrames()),
            loadLayerSpritesFn: createTestLoadLayerSpritesFn(),
            requestAnimationFrameFn: () => 0,
            audioDeps,
        };
        await init(deps);
        // Audio event listeners should be registered
        expect(audioDeps.handlers.get("click")?.length).toBe(1);
        expect(audioDeps.handlers.get("touchstart")?.length).toBe(1);
        expect(audioDeps.handlers.get("keydown")?.length).toBe(1);
    });
    it("does not initialize audio when disabled in config", async () => {
        const audioDeps = createTestAudioDeps();
        const configWithDisabledAudio = {
            ...createTestConfig(),
            audio: {
                enabled: false,
                masterVolume: 0.5,
                tracks: [{ id: "ambient", path: "audio/ambient.mp3", volume: 1.0, loop: true, tags: {} }],
            },
        };
        const deps = {
            getScreenElement: () => screen,
            loadConfigFn: () => Promise.resolve(configWithDisabledAudio),
            loadBunnyFramesFn: () => Promise.resolve(createTestBunnyFrames()),
            loadLayerSpritesFn: createTestLoadLayerSpritesFn(),
            requestAnimationFrameFn: () => 0,
            audioDeps,
        };
        await init(deps);
        // No event listeners should be registered
        expect(audioDeps.handlers.get("click")).toBeUndefined();
    });
});
describe("_test_hooks", () => {
    it("createDefaultDependencies returns functions", () => {
        const deps = _test_hooks.createDefaultDependencies();
        expect(typeof deps.getScreenElement).toBe("function");
        expect(typeof deps.loadConfigFn).toBe("function");
        expect(typeof deps.loadBunnyFramesFn).toBe("function");
        expect(typeof deps.loadLayerSpritesFn).toBe("function");
        expect(typeof deps.requestAnimationFrameFn).toBe("function");
        expect(typeof deps.audioDeps).toBe("object");
    });
    it("createDefaultDependencies getScreenElement returns null when no screen", () => {
        const deps = _test_hooks.createDefaultDependencies();
        // No #screen element in DOM
        const result = deps.getScreenElement();
        expect(result).toBeNull();
    });
    it("createDefaultDependencies getScreenElement returns element when present", () => {
        const screen = document.createElement("pre");
        screen.id = "screen";
        document.body.appendChild(screen);
        const deps = _test_hooks.createDefaultDependencies();
        const result = deps.getScreenElement();
        expect(result).toBe(screen);
        document.body.removeChild(screen);
    });
    it("isTestEnvironment returns true in test environment", () => {
        // When running under Vitest, this should return true
        expect(_test_hooks.isTestEnvironment()).toBe(true);
    });
    it("requestAnimationFrameFn schedules callback", () => {
        const deps = _test_hooks.createDefaultDependencies();
        const noop = () => { };
        const id = deps.requestAnimationFrameFn(noop);
        expect(typeof id).toBe("number");
        // Cancel to prevent callback from running after test
        cancelAnimationFrame(id);
    });
});
describe("createLayerAnimationCallback", () => {
    it("returns a callback that advances all scene sprite frames", () => {
        const entity = {
            spriteName: "test",
            sizes: [{ width: 10, frames: ["a", "b", "c"] }],
            sizeIdx: 0,
            frameIdx: 0,
            worldX: 0,
            worldZ: 100,
        };
        const layerConfig = {
            name: "test-layer",
            type: "sprites",
            layer: 10,
            spriteNames: ["test"],
            positions: [],
            zIndex: 0,
            tile: false,
            behavior: LAYER_BEHAVIORS.midground,
        };
        const layer = {
            config: layerConfig,
            entities: [entity],
        };
        const camera = createCamera();
        const depthBounds = createTestDepthBounds();
        const scene = createSceneState([layer], camera, depthBounds);
        const callback = createLayerAnimationCallback(scene);
        // Initial state
        expect(entity.frameIdx).toBe(0);
        // Call the callback
        callback();
        // Frame should have advanced
        expect(entity.frameIdx).toBe(1);
        // Call again
        callback();
        expect(entity.frameIdx).toBe(2);
    });
});
describe("advanceAllSceneSpriteFrames", () => {
    it("advances frame index for all entities in all layers", () => {
        const entity1 = {
            spriteName: "test1",
            sizes: [{ width: 10, frames: ["a", "b", "c"] }],
            sizeIdx: 0,
            frameIdx: 0,
            worldX: 0,
            worldZ: 100,
        };
        const entity2 = {
            spriteName: "test2",
            sizes: [{ width: 10, frames: ["x", "y"] }],
            sizeIdx: 0,
            frameIdx: 0,
            worldX: 50,
            worldZ: 100,
        };
        const layerConfig = {
            name: "test-layer",
            type: "sprites",
            layer: 10,
            spriteNames: ["test1", "test2"],
            positions: [],
            zIndex: 0,
            tile: false,
            behavior: LAYER_BEHAVIORS.midground,
        };
        const layer = {
            config: layerConfig,
            entities: [entity1, entity2],
        };
        const camera = createCamera();
        const depthBounds = createTestDepthBounds();
        const scene = createSceneState([layer], camera, depthBounds);
        // Initial state
        expect(entity1.frameIdx).toBe(0);
        expect(entity2.frameIdx).toBe(0);
        // Advance frames
        advanceAllSceneSpriteFrames(scene);
        // Both entities should have advanced
        expect(entity1.frameIdx).toBe(1);
        expect(entity2.frameIdx).toBe(1);
        // Advance again
        advanceAllSceneSpriteFrames(scene);
        // entity1 has 3 frames, entity2 has 2 frames (wraps to 0)
        expect(entity1.frameIdx).toBe(2);
        expect(entity2.frameIdx).toBe(0);
    });
    it("handles empty scene", () => {
        const camera = createCamera();
        const depthBounds = createTestDepthBounds();
        const scene = createSceneState([], camera, depthBounds);
        // Should not throw
        advanceAllSceneSpriteFrames(scene);
    });
    it("handles layer with no entities", () => {
        const layerConfig = {
            name: "empty-layer",
            type: "sprites",
            layer: 10,
            spriteNames: [],
            positions: [],
            zIndex: 0,
            tile: false,
            behavior: LAYER_BEHAVIORS.midground,
        };
        const layer = {
            config: layerConfig,
            entities: [],
        };
        const camera = createCamera();
        const depthBounds = createTestDepthBounds();
        const scene = createSceneState([layer], camera, depthBounds);
        // Should not throw
        advanceAllSceneSpriteFrames(scene);
    });
});
//# sourceMappingURL=main.test.js.map