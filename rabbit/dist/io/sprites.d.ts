/**
 * Sprite loading I/O code.
 * This module contains dynamic imports which require browser/bundler integration.
 * Excluded from unit test coverage - testability ensured through dependency injection.
 */
import type { Config, FrameSet } from "../types.js";
import type { BunnyFrames } from "../entities/Bunny.js";
import type { TreeSize } from "../entities/Tree.js";
import type { ValidatedLayer } from "../layers/types.js";
import type { SpriteRegistry } from "../loaders/layers.js";
/** Module interface for sprite frame exports */
export interface SpriteModule {
    readonly frames: readonly string[];
}
/**
 * Load sprite frames for animated sprites (with direction).
 */
export declare function loadSpriteFrames(spriteName: string, animationName: string, width: number, direction?: string): Promise<FrameSet>;
/**
 * Load sprite frames for static sprites (no direction).
 */
export declare function loadStaticSpriteFrames(spriteName: string, width: number): Promise<FrameSet>;
/**
 * Load config from JSON file.
 */
export declare function loadConfig(): Promise<Config>;
/**
 * Load all bunny animation frames.
 */
export declare function loadBunnyFrames(_config: Config): Promise<BunnyFrames>;
/**
 * Load all tree size variations.
 */
export declare function loadTreeSizes(_config: Config): Promise<TreeSize[]>;
/**
 * Load all sprites referenced by layers.
 */
export declare function loadLayerSprites(config: Config, layers: readonly ValidatedLayer[]): Promise<SpriteRegistry>;
//# sourceMappingURL=sprites.d.ts.map