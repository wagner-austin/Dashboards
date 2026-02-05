/**
 * Main entry point for the ASCII animation engine.
 * Orchestrates modules for rendering, entities, and input.
 */

import type { Config } from "./types.js";
import { measureViewport, type ViewportState } from "./rendering/Viewport.js";
import { renderFrame, type RenderState } from "./rendering/SceneRenderer.js";
import { createAnimationTimer } from "./loaders/sprites.js";
import { createInitialBunnyState, createBunnyTimers, type BunnyFrames } from "./entities/Bunny.js";
import { createInitialTreeState, createTreeTimer, type TreeSize } from "./entities/Tree.js";
import { setupKeyboardControls, type InputState } from "./input/Keyboard.js";
import { validateLayersConfig, createSceneState, type SceneState, type ValidatedLayer } from "./layers/index.js";
import { createLayerInstances, type SpriteRegistry } from "./loaders/layers.js";
import { createLayerAnimationCallback } from "./entities/SceneSprite.js";
import {
  initializeAudio,
  setupTrackSwitcher,
  type AudioDependencies,
} from "./audio/index.js";
import {
  loadConfig,
  loadBunnyFrames,
  loadTreeSizes,
  loadLayerSprites,
  createDefaultAudioDependencies,
} from "./io/index.js";

/** Dependencies that can be injected for testing */
export interface MainDependencies {
  getScreenElement: () => HTMLPreElement | null;
  loadConfigFn: () => Promise<Config>;
  loadBunnyFramesFn: (config: Config) => Promise<BunnyFrames>;
  loadTreeSizesFn: (config: Config) => Promise<TreeSize[]>;
  loadLayerSpritesFn: (config: Config, layers: readonly ValidatedLayer[]) => Promise<SpriteRegistry>;
  requestAnimationFrameFn: (callback: (time: number) => void) => number;
  audioDeps: AudioDependencies;
}

/** Default dependencies using real implementations */
function createDefaultDependencies(): MainDependencies {
  return {
    getScreenElement: () => document.getElementById("screen") as HTMLPreElement | null,
    loadConfigFn: loadConfig,
    loadBunnyFramesFn: loadBunnyFrames,
    loadTreeSizesFn: loadTreeSizes,
    loadLayerSpritesFn: loadLayerSprites,
    requestAnimationFrameFn: (callback) => requestAnimationFrame(callback),
    audioDeps: createDefaultAudioDependencies(),
  };
}

/** Initialize the application with injectable dependencies */
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
  const treeSizes = await deps.loadTreeSizesFn(config);

  // Validate and load layer sprites
  const validatedLayers = validateLayersConfig(config.layers);
  const layerRegistry = await deps.loadLayerSpritesFn(config, validatedLayers);
  const layerInstances = createLayerInstances(validatedLayers, layerRegistry, viewport.width);
  const sceneState = createSceneState(layerInstances);

  // Initialize state
  const bunnyState = createInitialBunnyState();
  const treeState = createInitialTreeState(viewport.width);

  const state: InputState & { viewport: ViewportState; groundScrollX: number; scene: SceneState } = {
    bunny: bunnyState,
    tree: treeState,
    viewport,
    groundScrollX: 0,
    scene: sceneState,
  };

  // Create timers
  const bunnyTimers = createBunnyTimers(bunnyState, bunnyFrames, {
    walk: 120,
    idle: 500,
    jump: 58,
    transition: 80,
  });
  const treeTimer = createTreeTimer(treeState, treeSizes, 250);

  // Layer animation timer - advances all scene sprite frames
  const layerAnimationCallback = createLayerAnimationCallback(sceneState);
  const layerAnimationTimer = createAnimationTimer(400, layerAnimationCallback);

  // Setup input
  setupKeyboardControls(state, bunnyFrames, bunnyTimers, treeSizes);

  // Handle resize
  window.addEventListener("resize", () => {
    state.viewport = measureViewport(screen);
  });

  // Initialize audio (will start on first user interaction)
  const audioSystem = initializeAudio(config.audio, deps.audioDeps);
  if (audioSystem !== null) {
    setupTrackSwitcher(audioSystem, (type, handler) => {
      document.addEventListener(type, handler);
    });
  }

  // Start timers
  bunnyTimers.walk.start();
  bunnyTimers.idle.start();
  treeTimer.start();
  layerAnimationTimer.start();

  // Render loop
  const SCROLL_SPEED = config.settings.scrollSpeed;
  const TREE_TRANSITION_DURATION_MS = 800;
  let lastTime = 0;

  function render(currentTime: number): void {
    const renderState: RenderState = {
      bunnyState,
      treeState,
      sceneState: state.scene,
      viewport: state.viewport,
      groundScrollX: state.groundScrollX,
      lastTime,
    };

    const result = renderFrame(
      renderState,
      bunnyFrames,
      treeSizes,
      screen,
      currentTime,
      SCROLL_SPEED,
      TREE_TRANSITION_DURATION_MS
    );

    state.groundScrollX = result.groundScrollX;
    lastTime = result.lastTime;

    deps.requestAnimationFrameFn(render);
  }

  deps.requestAnimationFrameFn(render);
}

// Vitest sets import.meta.env.MODE to 'test'
function isTestEnvironment(): boolean {
  const meta = import.meta as { env?: { MODE?: string } };
  return meta.env?.MODE === "test";
}

/** Test hooks for internal functions */
export const _test_hooks = {
  createDefaultDependencies,
  isTestEnvironment,
};
