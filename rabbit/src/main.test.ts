/**
 * @vitest-environment jsdom
 * Tests for main entry point.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { init, _test_hooks, type MainDependencies } from "./main.js";
import { advanceAllSceneSpriteFrames, createLayerAnimationCallback } from "./entities/SceneSprite.js";
import type { BunnyFrames } from "./entities/Bunny.js";
import type { LayerInstance, SceneSpriteState, ValidatedLayer as LayerValidatedLayer } from "./layers/types.js";
import { createSceneState } from "./layers/index.js";
import type { SpriteRegistry } from "./loaders/layers.js";
import type { Config } from "./types.js";
import type { ValidatedLayer } from "./layers/types.js";
import type { AudioDependencies } from "./audio/index.js";
import { createCamera } from "./world/Projection.js";

function createTestBunnyFrames(): BunnyFrames {
  return {
    walkLeft: ["walk_l_0", "walk_l_1"],
    walkRight: ["walk_r_0", "walk_r_1"],
    jumpLeft: ["jump_l_0"],
    jumpRight: ["jump_r_0"],
    idleLeft: ["idle_l_0"],
    idleRight: ["idle_r_0"],
    walkToIdleLeft: ["trans_l_0", "trans_l_1"],
    walkToIdleRight: ["trans_r_0", "trans_r_1"],
  };
}

function createTestConfig(): Config {
  return {
    sprites: {},
    layers: [],
    settings: { fps: 60, jumpSpeed: 10, scrollSpeed: 100 },
  };
}

function createTestSpriteRegistry(): SpriteRegistry {
  return { sprites: new Map() };
}

function createTestLoadLayerSpritesFn(): (_config: Config, _layers: readonly ValidatedLayer[]) => Promise<SpriteRegistry> {
  return () => Promise.resolve(createTestSpriteRegistry());
}

/** Test audio element interface */
interface TestAudioElement {
  src: string;
  volume: number;
  loop: boolean;
  play: () => Promise<void>;
  pause: () => void;
}

/** Test audio deps return type */
interface TestAudioDeps extends AudioDependencies {
  handlers: Map<string, (() => void)[]>;
}

/** Create test audio dependencies with no-op event listeners */
function createTestAudioDeps(): TestAudioDeps {
  const handlers = new Map<string, (() => void)[]>();
  return {
    createElementFn: (): TestAudioElement => ({
      src: "",
      volume: 1,
      loop: false,
      play: (): Promise<void> => Promise.resolve(),
      pause: (): void => { /* no-op */ },
    }),
    addEventListenerFn: (type: string, handler: () => void): void => {
      const existing = handlers.get(type) ?? [];
      existing.push(handler);
      handlers.set(type, existing);
    },
    removeEventListenerFn: (type: string, handler: () => void): void => {
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
  let screen: HTMLPreElement;
  let rafCallbacks: ((time: number) => void)[];

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
    const deps: MainDependencies = {
      getScreenElement: () => null,
      loadConfigFn: () => Promise.resolve(createTestConfig()),
      loadBunnyFramesFn: () => Promise.resolve(createTestBunnyFrames()),
      loadLayerSpritesFn: createTestLoadLayerSpritesFn(),
      requestAnimationFrameFn: () => 0,
      audioDeps: createTestAudioDeps(),
    };

    await expect(init(deps)).rejects.toThrow("Screen element not found");
  });

  it("initializes and starts render loop", async () => {
    const deps: MainDependencies = {
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
    const deps: MainDependencies = {
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

    const deps: MainDependencies = {
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

    const deps: MainDependencies = {
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
    const noop = (): void => { /* scheduled callback */ };
    const id = deps.requestAnimationFrameFn(noop);
    expect(typeof id).toBe("number");
    // Cancel to prevent callback from running after test
    cancelAnimationFrame(id);
  });

});

describe("createLayerAnimationCallback", () => {
  it("returns a callback that advances all scene sprite frames", () => {
    const entity: SceneSpriteState = {
      spriteName: "test",
      sizes: [{ width: 10, frames: ["a", "b", "c"] }],
      sizeIdx: 0,
      frameIdx: 0,
      worldX: 0,
      worldZ: 100,
    };
    const layerConfig: LayerValidatedLayer = {
      name: "test-layer",
      type: "sprites",
      layer: 10,
      spriteNames: ["test"],
      positions: [],
      zIndex: 0,
      tile: false,
    };
    const layer: LayerInstance = {
      config: layerConfig,
      entities: [entity],
    };
    const camera = createCamera();
    const scene = createSceneState([layer], camera);

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
    const entity1: SceneSpriteState = {
      spriteName: "test1",
      sizes: [{ width: 10, frames: ["a", "b", "c"] }],
      sizeIdx: 0,
      frameIdx: 0,
      worldX: 0,
      worldZ: 100,
    };
    const entity2: SceneSpriteState = {
      spriteName: "test2",
      sizes: [{ width: 10, frames: ["x", "y"] }],
      sizeIdx: 0,
      frameIdx: 0,
      worldX: 50,
      worldZ: 100,
    };
    const layerConfig: LayerValidatedLayer = {
      name: "test-layer",
      type: "sprites",
      layer: 10,
      spriteNames: ["test1", "test2"],
      positions: [],
      zIndex: 0,
      tile: false,
    };
    const layer: LayerInstance = {
      config: layerConfig,
      entities: [entity1, entity2],
    };
    const camera = createCamera();
    const scene = createSceneState([layer], camera);

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
    const scene = createSceneState([], camera);
    // Should not throw
    advanceAllSceneSpriteFrames(scene);
  });

  it("handles layer with no entities", () => {
    const layerConfig: LayerValidatedLayer = {
      name: "empty-layer",
      type: "sprites",
      layer: 10,
      spriteNames: [],
      positions: [],
      zIndex: 0,
      tile: false,
    };
    const layer: LayerInstance = {
      config: layerConfig,
      entities: [],
    };
    const camera = createCamera();
    const scene = createSceneState([layer], camera);
    // Should not throw
    advanceAllSceneSpriteFrames(scene);
  });
});
