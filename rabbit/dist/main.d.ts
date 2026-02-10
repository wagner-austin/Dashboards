/**
 * Main entry point for the ASCII animation engine.
 *
 * Orchestrates modules for rendering, entities, and input.
 */
import type { Config } from "./types.js";
import { type BunnyFrames } from "./entities/Bunny.js";
import { type ValidatedLayer } from "./layers/index.js";
import { type SpriteRegistry } from "./loaders/layers.js";
import { type AudioDependencies } from "./audio/index.js";
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
declare function createDefaultDependencies(): MainDependencies;
/**
 * Initialize the application with injectable dependencies.
 *
 * Args:
 *     deps: Dependencies for testing or production.
 *
 * Raises:
 *     Error: If screen element not found.
 */
export declare function init(deps?: MainDependencies): Promise<void>;
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
};
export {};
//# sourceMappingURL=main.d.ts.map