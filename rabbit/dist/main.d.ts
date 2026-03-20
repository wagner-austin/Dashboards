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
import { type AudioDependencies } from "./audio/index.js";
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
    runProgressiveLoadFn: (config: Config, registry: MutableSpriteRegistry, onProgress: ProgressCallback, onBunnyLoaded: BunnyLoadedCallback) => Promise<void>;
    requestAnimationFrameFn: (callback: (time: number) => void) => number;
    audioDeps: AudioDependencies;
}
/**
 * Create default dependencies using real implementations.
 *
 * Returns:
 *     MainDependencies with browser implementations.
 */
declare function createDefaultDependencies(): MainDependencies;
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
declare function collectAllSpriteNames(config: Config): readonly string[];
/**
 * Initialize the application with progressive loading.
 *
 * Starts render loop immediately with ground visible, then progressively
 * loads grass, bunny, and trees (smallest to largest). Scene populates
 * as sprites load.
 *
 * Args:
 *     deps: Dependencies for testing or production.
 *
 * Raises:
 *     Error: If screen element not found or autoLayers not configured.
 */
export declare function init(deps?: MainDependencies): Promise<void>;
/**
 * Create empty bunny frames for rendering before bunny is loaded.
 *
 * Returns:
 *     BunnyFrames with empty arrays for all animations.
 */
declare function createEmptyBunnyFrames(): BunnyFrames;
/**
 * Check if running in test environment.
 *
 * Returns:
 *     True if MODE is 'test'.
 */
declare function isTestEnvironment(): boolean;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createDefaultDependencies: typeof createDefaultDependencies;
    isTestEnvironment: typeof isTestEnvironment;
    collectAllSpriteNames: typeof collectAllSpriteNames;
    createEmptyBunnyFrames: typeof createEmptyBunnyFrames;
};
export {};
//# sourceMappingURL=main.d.ts.map