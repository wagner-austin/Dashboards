/**
 * Main entry point for the ASCII animation engine.
 *
 * Orchestrates modules for rendering, entities, and input.
 */

import type { Config } from "./types.js";
import { measureViewport, type ViewportState } from "./rendering/Viewport.js";
import { renderFrame, type RenderState } from "./rendering/SceneRenderer.js";
import { createAnimationTimer } from "./loaders/sprites.js";
import { createInitialBunnyState, createBunnyTimers, type BunnyFrames } from "./entities/Bunny.js";
import { setupKeyboardControls, processDepthMovement, processHorizontalMovement, type InputState } from "./input/Keyboard.js";
import { processLayersConfig, createSceneState, type SceneState, type ValidatedLayer } from "./layers/index.js";
import { createLayerInstances, type SpriteRegistry } from "./loaders/layers.js";
import { createLayerAnimationCallback } from "./entities/SceneSprite.js";
import { createCamera, createProjectionConfig } from "./world/Projection.js";
import {
  initializeAudio,
  setupTrackSwitcher,
  type AudioDependencies,
} from "./audio/index.js";
import {
  loadConfig,
  loadBunnyFrames,
  loadLayerSprites,
  createDefaultAudioDependencies,
} from "./io/index.js";

/**
 * Dependencies that can be injected for testing.
 *
 * getScreenElement: Returns the pre element for rendering.
 * loadConfigFn: Loads the config.json file.
 * loadBunnyFramesFn: Loads bunny animation frames.
 * loadLayerSpritesFn: Loads layer sprite data.
 * requestAnimationFrameFn: Schedules next frame.
 * audioDeps: Audio system dependencies.
 */
export interface MainDependencies {
  getScreenElement: () => HTMLPreElement | null;
  loadConfigFn: () => Promise<Config>;
  loadBunnyFramesFn: (config: Config) => Promise<BunnyFrames>;
  loadLayerSpritesFn: (config: Config, layers: readonly ValidatedLayer[]) => Promise<SpriteRegistry>;
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
    loadBunnyFramesFn: loadBunnyFrames,
    loadLayerSpritesFn: loadLayerSprites,
    requestAnimationFrameFn: (callback) => requestAnimationFrame(callback),
    audioDeps: createDefaultAudioDependencies(),
  };
}

/**
 * Initialize the application with injectable dependencies.
 *
 * Args:
 *     deps: Dependencies for testing or production.
 *
 * Raises:
 *     Error: If screen element not found.
 */
export async function init(deps: MainDependencies = createDefaultDependencies()): Promise<void> {
  const config = await deps.loadConfigFn();
  const screenEl = deps.getScreenElement();

  if (screenEl === null) {
    throw new Error("Screen element not found");
  }

  const screen = screenEl;
  const viewport = measureViewport(screen);

  // Load sprites
  const bunnyFrames = await deps.loadBunnyFramesFn(config);

  // Process layers (including auto-generated layers if configured)
  const validatedLayers = processLayersConfig(config.layers, config.autoLayers);
  const layerRegistry = await deps.loadLayerSpritesFn(config, validatedLayers);
  const layerInstances = createLayerInstances(validatedLayers, layerRegistry, viewport.width);

  // Create camera and projection config
  const camera = createCamera();
  const projectionConfig = createProjectionConfig();

  // Create scene state with camera
  const sceneState = createSceneState(layerInstances, camera);

  // Initialize entity state
  const bunnyState = createInitialBunnyState();

  const state: InputState & { viewport: ViewportState; scene: SceneState } = {
    bunny: bunnyState,
    viewport,
    camera,
    hopKeyHeld: null,
    slideKeyHeld: null,
    scene: sceneState,
  };

  // Create timers
  const bunnyTimers = createBunnyTimers(bunnyState, bunnyFrames, {
    walk: 120,
    idle: 500,
    jump: 58,
    transition: 50,
    hop: 150,
  });

  // Layer animation timer
  const layerAnimationCallback = createLayerAnimationCallback(sceneState);
  const layerAnimationTimer = createAnimationTimer(400, layerAnimationCallback);

  // Setup keyboard input
  setupKeyboardControls(state, bunnyFrames, bunnyTimers);

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

  // Start timers
  bunnyTimers.walk.start();
  bunnyTimers.idle.start();
  layerAnimationTimer.start();

  // Render loop
  const SCROLL_SPEED = config.settings.scrollSpeed;
  let lastTime = 0;

  function render(currentTime: number): void {
    // Process movement input (continuous while keys held)
    processDepthMovement(state);
    processHorizontalMovement(state);

    // Sync camera from input state to scene state
    state.scene.camera = state.camera;

    const renderState: RenderState = {
      bunnyState,
      sceneState: state.scene,
      viewport: state.viewport,
      lastTime,
      projectionConfig,
    };

    const result = renderFrame(
      renderState,
      bunnyFrames,
      screen,
      currentTime,
      SCROLL_SPEED
    );

    // Sync camera back from scene state to input state
    state.camera = state.scene.camera;
    lastTime = result.lastTime;

    deps.requestAnimationFrameFn(render);
  }

  deps.requestAnimationFrameFn(render);
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
};
