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
import type { MutableSpriteRegistry, ProgressCallback } from "../loaders/progressive.js";
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
 * Load all tree size variations from config.
 *
 * Reads tree sprite widths from config and loads each size.
 * Returns sizes sorted smallest to largest.
 *
 * Args:
 *     config: Application config with sprite definitions.
 *
 * Returns:
 *     Array of TreeSize sorted by width ascending.
 */
export declare function loadTreeSizes(config: Config): Promise<TreeSize[]>;
/**
 * Load all sprites referenced by layers.
 */
export declare function loadLayerSprites(config: Config, layers: readonly ValidatedLayer[]): Promise<SpriteRegistry>;
/**
 * Load grass sprites into mutable registry.
 *
 * Args:
 *     config: Application config.
 *     registry: Mutable sprite registry.
 *     onProgress: Progress callback.
 */
export declare function loadGrassSprites(config: Config, registry: MutableSpriteRegistry, onProgress: ProgressCallback): Promise<void>;
/**
 * Load tree sprites progressively from largest to smallest.
 *
 * Loads trees interleaved across tree types (tree1, tree2, etc.)
 * so that the largest trees from all types load first.
 *
 * Args:
 *     config: Application config.
 *     registry: Mutable sprite registry.
 *     onProgress: Progress callback.
 */
export declare function loadTreeSpritesProgressive(config: Config, registry: MutableSpriteRegistry, onProgress: ProgressCallback): Promise<void>;
/**
 * Callback invoked when bunny frames finish loading.
 */
export type BunnyLoadedCallback = (frames: BunnyFrames) => void;
/**
 * Run progressive loading sequence.
 *
 * Loads sprites in order: ground, grass, bunny, trees (largest to smallest).
 * Calls onProgress for each loaded sprite to enable UI updates.
 * Calls onBunnyLoaded immediately when bunny frames are ready, before trees.
 *
 * Args:
 *     config: Application config.
 *     registry: Mutable sprite registry to populate.
 *     onProgress: Progress callback for each loaded sprite.
 *     onBunnyLoaded: Callback when bunny frames are ready (before trees load).
 */
export declare function runProgressiveLoad(config: Config, registry: MutableSpriteRegistry, onProgress: ProgressCallback, onBunnyLoaded: BunnyLoadedCallback): Promise<void>;
//# sourceMappingURL=sprites.d.ts.map