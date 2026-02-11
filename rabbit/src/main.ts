/**
 * Main entry point for the ASCII animation engine.
 *
 * Orchestrates modules for rendering, entities, and input.
 * Uses progressive loading to populate scene as sprites load.
 */

import type { Config } from "./types.js";
import type { BunnyFrames } from "./entities/Bunny.js";
import type { MutableSpriteRegistry, ProgressCallback } from "./loaders/progressive.js";
import type { BunnyLoadedCallback } from "./io/sprites.js";
import { measureViewport, type ViewportState } from "./rendering/Viewport.js";
import { renderFrame, type RenderState } from "./rendering/SceneRenderer.js";
import { createAnimationTimer } from "./loaders/sprites.js";
import { createInitialBunnyState, createBunnyTimers } from "./entities/Bunny.js";
import { setupKeyboardControls, processDepthMovement, processHorizontalMovement, processWalkMovement, type InputState } from "./input/Keyboard.js";
import { processLayersConfig, createSceneState, type SceneState } from "./layers/index.js";
import { createProgressiveLayerInstances } from "./loaders/layers.js";
import { createLayerAnimationCallback } from "./entities/SceneSprite.js";
import { createCamera, createProjectionConfig, calculateDepthBounds } from "./world/Projection.js";
import { layerToWorldZ } from "./layers/widths.js";
import { createMutableSpriteRegistry } from "./loaders/progressive.js";
import {
  initializeAudio,
  setupTrackSwitcher,
  type AudioDependencies,
} from "./audio/index.js";
import {
  loadConfig,
  runProgressiveLoad,
  createDefaultAudioDependencies,
} from "./io/index.js";

/**
 * Dependencies that can be injected for testing.
 *
 * getScreenElement: Returns the pre element for rendering.
 * loadConfigFn: Loads the config.json file.
 * runProgressiveLoadFn: Runs progressive sprite loading.
 * requestAnimationFrameFn: Schedules next frame.
 * audioDeps: Audio system dependencies.
 */
export interface MainDependencies {
  getScreenElement: () => HTMLPreElement | null;
  loadConfigFn: () => Promise<Config>;
  runProgressiveLoadFn: (
    config: Config,
    registry: MutableSpriteRegistry,
    onProgress: ProgressCallback,
    onBunnyLoaded: BunnyLoadedCallback
  ) => Promise<void>;
  requestAnimationFrameFn: (callback: (time: number) => void) => number;
  audioDeps: AudioDependencies;
}

/**
 * Create default dependencies using real implementations.
 *
 * Returns:
 *     MainDependencies with browser implementations.
 */
function createDefaultDependencies(): MainDependencies {
  return {
    getScreenElement: () => document.getElementById("screen") as HTMLPreElement | null,
    loadConfigFn: loadConfig,
    runProgressiveLoadFn: runProgressiveLoad,
    requestAnimationFrameFn: (callback) => requestAnimationFrame(callback),
    audioDeps: createDefaultAudioDependencies(),
  };
}

/**
 * Collect all sprite names referenced in config.
 *
 * Gathers sprite names from both manual layers and autoLayers config.
 *
 * Args:
 *     config: Application config.
 *
 * Returns:
 *     Array of unique sprite names.
 */
function collectAllSpriteNames(config: Config): readonly string[] {
  const names = new Set<string>();

  // From manual layers
  for (const layer of config.layers) {
    if (layer.sprites !== undefined) {
      for (const name of layer.sprites) {
        names.add(name);
      }
    }
  }

  // From autoLayers
  if (config.autoLayers !== undefined) {
    for (const name of config.autoLayers.sprites) {
      names.add(name);
    }
  }

  return [...names];
}

/**
 * Initialize the application with progressive loading.
 *
 * Starts render loop immediately with ground visible, then progressively
 * loads grass, bunny, and trees (largest to smallest). Scene populates
 * as sprites load.
 *
 * Args:
 *     deps: Dependencies for testing or production.
 *
 * Raises:
 *     Error: If screen element not found or autoLayers not configured.
 */
export async function init(deps: MainDependencies = createDefaultDependencies()): Promise<void> {
  const config = await deps.loadConfigFn();
  const screenEl = deps.getScreenElement();

  if (screenEl === null) {
    throw new Error("Screen element not found");
  }

  const screen = screenEl;
  const viewport = measureViewport(screen);

  // Require autoLayers config for depth bounds
  if (config.autoLayers === undefined) {
    throw new Error("config.autoLayers is required for depth movement");
  }

  // Create mutable sprite registry with all sprite names
  const spriteNames = collectAllSpriteNames(config);
  const spriteRegistry = createMutableSpriteRegistry(spriteNames);

  // Process layers (including auto-generated layers if configured)
  const validatedLayers = processLayersConfig(config.layers, config.autoLayers);

  // Create layer instances with mutable registry (entities start with empty sizes)
  const layerInstances = createProgressiveLayerInstances(validatedLayers, spriteRegistry, viewport.width);

  // Create camera and projection config
  const camera = createCamera();
  const projectionConfig = createProjectionConfig();

  // Calculate depth bounds from autoLayers config
  const minTreeWorldZ = layerToWorldZ(config.autoLayers.minLayer);
  const maxTreeWorldZ = layerToWorldZ(config.autoLayers.maxLayer);
  const depthBounds = calculateDepthBounds(minTreeWorldZ, maxTreeWorldZ, projectionConfig);

  // Create scene state with camera and depth bounds
  const sceneState = createSceneState(layerInstances, camera, depthBounds);

  // Initialize entity state (bunny state starts with no frames)
  const bunnyState = createInitialBunnyState();

  // Mutable reference for bunny frames (set when bunny loading completes)
  let bunnyFrames: BunnyFrames | null = null;

  const state: InputState & { viewport: ViewportState; scene: SceneState } = {
    bunny: bunnyState,
    viewport,
    camera,
    depthBounds,
    hopKeyHeld: null,
    slideKeyHeld: null,
    walkKeyHeld: null,
    scene: sceneState,
  };

  // Handle resize
  window.addEventListener("resize", () => {
    state.viewport = measureViewport(screen);
  });

  // Initialize audio
  const audioSystem = initializeAudio(config.audio, deps.audioDeps);
  if (audioSystem !== null) {
    setupTrackSwitcher(audioSystem, (type, handler) => {
      document.addEventListener(type, handler);
    });
  }

  // Layer animation timer
  const layerAnimationCallback = createLayerAnimationCallback(sceneState);
  const layerAnimationTimer = createAnimationTimer(400, layerAnimationCallback);
  layerAnimationTimer.start();

  // Render loop - starts immediately (ground visible, sprites appear as they load)
  const SCROLL_SPEED = config.settings.scrollSpeed;
  let lastTime = 0;

  function render(currentTime: number): void {
    // Process movement input only if bunny is loaded
    if (bunnyFrames !== null) {
      processDepthMovement(state);
      processHorizontalMovement(state);
      processWalkMovement(state);
    }

    // Sync camera from input state to scene state
    state.scene.camera = state.camera;

    const renderState: RenderState = {
      bunnyState,
      sceneState: state.scene,
      viewport: state.viewport,
      lastTime,
      projectionConfig,
    };

    // Only render bunny if frames are loaded
    if (bunnyFrames !== null) {
      const result = renderFrame(
        renderState,
        bunnyFrames,
        screen,
        currentTime,
        SCROLL_SPEED
      );
      lastTime = result.lastTime;
    } else {
      // Render without bunny (just layers and ground)
      const result = renderFrame(
        renderState,
        createEmptyBunnyFrames(),
        screen,
        currentTime,
        SCROLL_SPEED
      );
      lastTime = result.lastTime;
    }

    // Sync camera back from scene state to input state
    state.camera = state.scene.camera;

    deps.requestAnimationFrameFn(render);
  }

  // Start render loop immediately
  deps.requestAnimationFrameFn(render);

  // Run progressive loading in parallel (sprites appear as they load)
  await deps.runProgressiveLoadFn(
    config,
    spriteRegistry,
    (_progress) => {
      // Progress callback - could update a loading indicator here
      // Sprites are automatically visible as they're added to registry
    },
    (loadedBunnyFrames) => {
      // Bunny loaded callback - set up controls immediately
      bunnyFrames = loadedBunnyFrames;

      // Create timers now that bunny is loaded
      const bunnyTimers = createBunnyTimers(bunnyState, bunnyFrames, {
        walk: 120,
        idle: 500,
        jump: 58,
        transition: 50,
        hop: 150,
      });

      // Setup keyboard input
      setupKeyboardControls(state, bunnyFrames, bunnyTimers);

      // Start bunny animation timers
      bunnyTimers.walk.start();
      bunnyTimers.idle.start();
    }
  );
}

/**
 * Create empty bunny frames for rendering before bunny is loaded.
 *
 * Returns:
 *     BunnyFrames with empty arrays for all animations.
 */
function createEmptyBunnyFrames(): BunnyFrames {
  const empty: readonly string[] = [];
  return {
    walkLeft: empty,
    walkRight: empty,
    jumpLeft: empty,
    jumpRight: empty,
    idleLeft: empty,
    idleRight: empty,
    walkToIdleLeft: empty,
    walkToIdleRight: empty,
    walkToTurnAwayLeft: empty,
    walkToTurnAwayRight: empty,
    walkToTurnTowardLeft: empty,
    walkToTurnTowardRight: empty,
    hopAway: empty,
    hopToward: empty,
  };
}

/**
 * Check if running in test environment.
 *
 * Returns:
 *     True if MODE is 'test'.
 */
function isTestEnvironment(): boolean {
  const meta = import.meta as { env?: { MODE?: string } };
  return meta.env?.MODE === "test";
}

/** Test hooks for internal functions */
export const _test_hooks = {
  createDefaultDependencies,
  isTestEnvironment,
  collectAllSpriteNames,
  createEmptyBunnyFrames,
};
