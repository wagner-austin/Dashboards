/**
 * Main entry point for the ASCII animation engine.
 * Orchestrates modules for rendering, entities, and input.
 */
import type { Config } from "./types.js";
import { type BunnyFrames } from "./entities/Bunny.js";
import { type TreeSize } from "./entities/Tree.js";
import { type ValidatedLayer } from "./layers/index.js";
import { type SpriteRegistry } from "./loaders/layers.js";
import { type AudioDependencies } from "./audio/index.js";
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
declare function createDefaultDependencies(): MainDependencies;
/** Initialize the application with injectable dependencies */
export declare function init(deps?: MainDependencies): Promise<void>;
declare function isTestEnvironment(): boolean;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createDefaultDependencies: typeof createDefaultDependencies;
    isTestEnvironment: typeof isTestEnvironment;
};
export {};
//# sourceMappingURL=main.d.ts.map