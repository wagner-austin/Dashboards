/**
 * Progressive sprite loading for scene population.
 *
 * Loads sprites in a controlled order to populate scene progressively:
 * 1. Ground (instant - pure ASCII)
 * 2. Grass sprites
 * 3. Bunny animation frames
 * 4. Trees from largest to smallest width
 */
import type { Config, FrameSet } from "../types.js";
/**
 * Load phase for progressive loading.
 *
 * ground: ASCII ground (instant).
 * grass: Grass sprite widths.
 * bunny: All bunny animation frames.
 * trees: Tree widths from largest to smallest.
 */
export type LoadPhase = "ground" | "grass" | "bunny" | "trees";
/**
 * Tree width entry for ordered loading.
 *
 * spriteName: Name of tree sprite (tree1 or tree2).
 * width: Width to load.
 */
export interface TreeWidthEntry {
    readonly spriteName: string;
    readonly width: number;
}
/**
 * Progress update for loading callbacks.
 *
 * phase: Current load phase.
 * current: Current item index within phase.
 * total: Total items in phase.
 * spriteName: Name of sprite being loaded.
 * width: Width being loaded (for sprites with widths).
 */
export interface LoadProgress {
    readonly phase: LoadPhase;
    readonly current: number;
    readonly total: number;
    readonly spriteName: string;
    readonly width: number;
}
/**
 * Callback for load progress updates.
 */
export type ProgressCallback = (progress: LoadProgress) => void;
/**
 * Mutable sprite registry for progressive loading.
 *
 * Holds mutable FrameSet arrays that can be populated incrementally.
 * Entities hold references to these arrays and see new frames as they load.
 */
export interface MutableSpriteRegistry {
    readonly sprites: Map<string, FrameSet[]>;
}
/**
 * Create empty mutable sprite registry.
 *
 * Args:
 *     spriteNames: Names of sprites to create entries for.
 *
 * Returns:
 *     MutableSpriteRegistry with empty arrays for each sprite.
 */
export declare function createMutableSpriteRegistry(spriteNames: readonly string[]): MutableSpriteRegistry;
/**
 * Get or create sprite array in registry.
 *
 * Args:
 *     registry: Mutable sprite registry.
 *     spriteName: Name of sprite.
 *
 * Returns:
 *     Mutable FrameSet array for the sprite.
 */
export declare function getOrCreateSpriteArray(registry: MutableSpriteRegistry, spriteName: string): FrameSet[];
/**
 * Insert frame set into sorted position by width.
 *
 * Maintains ascending width order in the array.
 *
 * Args:
 *     sizes: Mutable array of frame sets.
 *     frameSet: Frame set to insert.
 */
export declare function insertSortedByWidth(sizes: FrameSet[], frameSet: FrameSet): void;
/**
 * Collect all tree widths from config, sorted descending (largest first).
 *
 * Combines widths from all tree sprites and returns unique widths
 * with their sprite names, sorted by width descending.
 *
 * Args:
 *     config: Application config with sprite definitions.
 *     treeNames: Names of tree sprites to collect widths from.
 *
 * Returns:
 *     Array of TreeWidthEntry sorted by width descending.
 */
export declare function collectTreeWidths(config: Config, treeNames: readonly string[]): readonly TreeWidthEntry[];
/**
 * Get grass sprite names from config layers.
 *
 * Args:
 *     config: Application config with layer definitions.
 *
 * Returns:
 *     Array of grass sprite names.
 */
export declare function getGrassSpriteNames(config: Config): readonly string[];
/**
 * Get tree sprite names from autoLayers config.
 *
 * Args:
 *     config: Application config with autoLayers.
 *
 * Returns:
 *     Array of tree sprite names, or empty if no autoLayers.
 */
export declare function getTreeSpriteNames(config: Config): readonly string[];
/**
 * Get sprite widths from config.
 *
 * Args:
 *     config: Application config.
 *     spriteName: Name of sprite.
 *
 * Returns:
 *     Array of widths, or empty if sprite not found.
 */
export declare function getSpriteWidthsFromConfig(config: Config, spriteName: string): readonly number[];
/** Test hooks for internal functions. */
export declare const _test_hooks: {
    createMutableSpriteRegistry: typeof createMutableSpriteRegistry;
    getOrCreateSpriteArray: typeof getOrCreateSpriteArray;
    insertSortedByWidth: typeof insertSortedByWidth;
    collectTreeWidths: typeof collectTreeWidths;
    getGrassSpriteNames: typeof getGrassSpriteNames;
    getTreeSpriteNames: typeof getTreeSpriteNames;
    getSpriteWidthsFromConfig: typeof getSpriteWidthsFromConfig;
};
//# sourceMappingURL=progressive.d.ts.map