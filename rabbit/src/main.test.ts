/**
 * @vitest-environment jsdom
 * Tests for main entry point.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { init, _test_hooks, type MainDependencies } from "./main.js";
import { advanceAllSceneSpriteFrames, createLayerAnimationCallback } from "./entities/SceneSprite.js";
import type { BunnyFrames } from "./entities/Bunny.js";
import type { LayerInstance, SceneSpriteState, ValidatedLayer } from "./layers/types.js";
import { createSceneState } from "./layers/index.js";
import type { MutableSpriteRegistry, ProgressCallback } from "./loaders/progressive.js";
import { LAYER_BEHAVIORS, type Config } from "./types.js";
import type { AudioDependencies } from "./audio/index.js";
import { createCamera, type DepthBounds } from "./world/Projection.js";

/** Test depth bounds (minZ=-110, maxZ=160, range=270) */
function createTestDepthBounds(): DepthBounds {
  return { minZ: -110, maxZ: 160, range: 270 };
}

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
    walkToTurnAwayLeft: ["turn_away_l_0", "turn_away_l_1"],
    walkToTurnAwayRight: ["turn_away_r_0", "turn_away_r_1"],
    walkToTurnTowardLeft: ["turn_toward_l_0", "turn_toward_l_1"],
    walkToTurnTowardRight: ["turn_toward_r_0", "turn_toward_r_1"],
    hopAway: ["hop_away_0", "hop_away_1"],
    hopToward: ["hop_toward_0", "hop_toward_1"],
  };
}

function createTestConfig(): Config {
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

/**
 * Create test runProgressiveLoadFn that calls onBunnyLoaded immediately.
 *
 * Calls the progress and bunny loaded callbacks to ensure code coverage.
 *
 * Args:
 *     bunnyFrames: BunnyFrames to pass to onBunnyLoaded.
 *
 * Returns:
 *     Function matching runProgressiveLoadFn signature.
 */
function createTestRunProgressiveLoadFn(
  bunnyFrames: BunnyFrames
): (_config: Config, _registry: MutableSpriteRegistry, _onProgress: ProgressCallback, onBunnyLoaded: (frames: BunnyFrames) => void) => Promise<void> {
  return (_config, _registry, onProgress, onBunnyLoaded) => {
    // Call progress callback to ensure coverage
    onProgress({ phase: "ground", current: 1, total: 1, spriteName: "ground", width: 0 });
    // Call bunny loaded callback
    onBunnyLoaded(bunnyFrames);
    return Promise.resolve();
  };
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
      runProgressiveLoadFn: createTestRunProgressiveLoadFn(createTestBunnyFrames()),
      requestAnimationFrameFn: () => 0,
      audioDeps: createTestAudioDeps(),
    };

    await expect(init(deps)).rejects.toThrow("Screen element not found");
  });

  it("throws when autoLayers not in config", async () => {
    const configWithoutAutoLayers: Config = {
      sprites: {},
      layers: [],
      settings: { fps: 60, jumpSpeed: 10, scrollSpeed: 100 },
      // No autoLayers
    };

    const deps: MainDependencies = {
      getScreenElement: () => screen,
      loadConfigFn: () => Promise.resolve(configWithoutAutoLayers),
      runProgressiveLoadFn: createTestRunProgressiveLoadFn(createTestBunnyFrames()),
      requestAnimationFrameFn: () => 0,
      audioDeps: createTestAudioDeps(),
    };

    await expect(init(deps)).rejects.toThrow("config.autoLayers is required for depth movement");
  });

  it("initializes and starts render loop", async () => {
    const deps: MainDependencies = {
      getScreenElement: () => screen,
      loadConfigFn: () => Promise.resolve(createTestConfig()),
      runProgressiveLoadFn: createTestRunProgressiveLoadFn(createTestBunnyFrames()),
      requestAnimationFrameFn: (callback) => {
        rafCallbacks.push(callback);
        return rafCallbacks.length;
      },
      audioDeps: createTestAudioDeps(),
    };

    await init(deps);

    // Should have queued multiple render callbacks (one at start, more as frames run)
    expect(rafCallbacks.length).toBeGreaterThanOrEqual(1);

    // Simulate frame
    const firstCallback = rafCallbacks[0];
    if (firstCallback === undefined) {
      throw new Error("Expected callback to be defined");
    }
    firstCallback(1000);

    // Should have queued another callback
    expect(rafCallbacks.length).toBeGreaterThan(1);
  });

  it("renders without bunny while loading", async () => {
    // Capture the onBunnyLoaded callback so we can control when it's called
    let capturedOnBunnyLoaded: (frames: BunnyFrames) => void = () => { /* placeholder */ };
    let resolveLoad: () => void = () => { /* placeholder */ };
    const loadPromise = new Promise<void>((resolve) => {
      resolveLoad = resolve;
    });

    const deps: MainDependencies = {
      getScreenElement: () => screen,
      loadConfigFn: () => Promise.resolve(createTestConfig()),
      runProgressiveLoadFn: (_config, _registry, onProgress, onBunnyLoaded) => {
        onProgress({ phase: "ground", current: 1, total: 1, spriteName: "ground", width: 0 });
        // Capture callback but don't call it yet - simulates bunny still loading
        capturedOnBunnyLoaded = onBunnyLoaded;
        return loadPromise;
      },
      requestAnimationFrameFn: (callback) => {
        rafCallbacks.push(callback);
        return rafCallbacks.length;
      },
      audioDeps: createTestAudioDeps(),
    };

    // Start init but don't await - it will block waiting for load
    const initPromise = init(deps);

    // Wait a tick for the first render callback to be queued
    await new Promise((resolve) => setTimeout(resolve, 0));

    // First render callback should be queued (before bunny loads)
    expect(rafCallbacks.length).toBeGreaterThanOrEqual(1);

    // Simulate frame while bunny is still loading
    const firstCallback = rafCallbacks[0];
    if (firstCallback === undefined) {
      throw new Error("Expected callback to be defined");
    }
    firstCallback(1000);

    // Screen should have rendered (without bunny, using empty frames)
    expect(screen.textContent).toBeDefined();

    // Should have queued another callback
    expect(rafCallbacks.length).toBeGreaterThan(1);

    // Now call the bunny loaded callback - simulates bunny finished loading
    capturedOnBunnyLoaded(createTestBunnyFrames());

    // Resolve the load promise to complete init
    resolveLoad();

    // Wait for init to complete
    await initPromise;

    // Run another frame - now with bunny loaded
    const laterCallback = rafCallbacks[rafCallbacks.length - 1];
    if (laterCallback !== undefined) {
      laterCallback(2000);
    }
  });

  it("handles resize event", async () => {
    const deps: MainDependencies = {
      getScreenElement: () => screen,
      loadConfigFn: () => Promise.resolve(createTestConfig()),
      runProgressiveLoadFn: createTestRunProgressiveLoadFn(createTestBunnyFrames()),
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
      runProgressiveLoadFn: createTestRunProgressiveLoadFn(createTestBunnyFrames()),
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
      runProgressiveLoadFn: createTestRunProgressiveLoadFn(createTestBunnyFrames()),
      requestAnimationFrameFn: () => 0,
      audioDeps,
    };

    await init(deps);

    // No event listeners should be registered
    expect(audioDeps.handlers.get("click")).toBeUndefined();
  });
});

describe("collectAllSpriteNames", () => {
  it("collects sprite names from manual layers", () => {
    const config: Config = {
      sprites: {},
      layers: [
        { name: "grass-front", sprites: ["grass"] },
        { name: "rocks", sprites: ["rock1", "rock2"] },
      ],
      settings: { fps: 60, jumpSpeed: 58, scrollSpeed: 36 },
    };

    const names = _test_hooks.collectAllSpriteNames(config);

    expect(names).toContain("grass");
    expect(names).toContain("rock1");
    expect(names).toContain("rock2");
  });

  it("collects sprite names from autoLayers", () => {
    const config: Config = {
      sprites: {},
      layers: [],
      settings: { fps: 60, jumpSpeed: 58, scrollSpeed: 36 },
      autoLayers: {
        sprites: ["tree1", "tree2"],
        minLayer: 8,
        maxLayer: 30,
      },
    };

    const names = _test_hooks.collectAllSpriteNames(config);

    expect(names).toContain("tree1");
    expect(names).toContain("tree2");
  });

  it("deduplicates sprite names", () => {
    const config: Config = {
      sprites: {},
      layers: [{ name: "layer1", sprites: ["tree1"] }],
      settings: { fps: 60, jumpSpeed: 58, scrollSpeed: 36 },
      autoLayers: {
        sprites: ["tree1", "tree2"],
        minLayer: 8,
        maxLayer: 30,
      },
    };

    const names = _test_hooks.collectAllSpriteNames(config);

    const tree1Count = names.filter((n) => n === "tree1").length;
    expect(tree1Count).toBe(1);
  });

  it("handles layers without sprites array", () => {
    const config: Config = {
      sprites: {},
      layers: [{ name: "sky", type: "static" }],
      settings: { fps: 60, jumpSpeed: 58, scrollSpeed: 36 },
    };

    const names = _test_hooks.collectAllSpriteNames(config);

    expect(names).toEqual([]);
  });
});

describe("createEmptyBunnyFrames", () => {
  it("returns BunnyFrames with empty arrays", () => {
    const frames = _test_hooks.createEmptyBunnyFrames();

    expect(frames.walkLeft).toEqual([]);
    expect(frames.walkRight).toEqual([]);
    expect(frames.jumpLeft).toEqual([]);
    expect(frames.jumpRight).toEqual([]);
    expect(frames.idleLeft).toEqual([]);
    expect(frames.idleRight).toEqual([]);
    expect(frames.walkToIdleLeft).toEqual([]);
    expect(frames.walkToIdleRight).toEqual([]);
    expect(frames.walkToTurnAwayLeft).toEqual([]);
    expect(frames.walkToTurnAwayRight).toEqual([]);
    expect(frames.walkToTurnTowardLeft).toEqual([]);
    expect(frames.walkToTurnTowardRight).toEqual([]);
    expect(frames.hopAway).toEqual([]);
    expect(frames.hopToward).toEqual([]);
  });
});

describe("_test_hooks", () => {
  it("createDefaultDependencies returns functions", () => {
    const deps = _test_hooks.createDefaultDependencies();
    expect(typeof deps.getScreenElement).toBe("function");
    expect(typeof deps.loadConfigFn).toBe("function");
    expect(typeof deps.runProgressiveLoadFn).toBe("function");
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
    const layerConfig: ValidatedLayer = {
      name: "test-layer",
      type: "sprites",
      layer: 10,
      spriteNames: ["test"],
      positions: [],
      zIndex: 0,
      tile: false,
      behavior: LAYER_BEHAVIORS.midground,
    };
    const layer: LayerInstance = {
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
    const layerConfig: ValidatedLayer = {
      name: "test-layer",
      type: "sprites",
      layer: 10,
      spriteNames: ["test1", "test2"],
      positions: [],
      zIndex: 0,
      tile: false,
      behavior: LAYER_BEHAVIORS.midground,
    };
    const layer: LayerInstance = {
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
    const layerConfig: ValidatedLayer = {
      name: "empty-layer",
      type: "sprites",
      layer: 10,
      spriteNames: [],
      positions: [],
      zIndex: 0,
      tile: false,
      behavior: LAYER_BEHAVIORS.midground,
    };
    const layer: LayerInstance = {
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
