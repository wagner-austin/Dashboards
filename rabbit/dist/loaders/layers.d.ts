/**
 * Layer loading from config.
 *
 * Dynamically loads sprite frames based on config and creates
 * layer instances with entities at specified positions.
 */
import type { Config, FrameSet, TreeZoomConfig, LayerSpriteConfig } from "../types.js";
import type { ValidatedLayer, LayerInstance } from "../layers/types.js";
/** Registry of loaded sprite frames by name */
export interface SpriteRegistry {
    readonly sprites: ReadonlyMap<string, readonly FrameSet[]>;
}
/**
 * Calculate sprite widths from zoom config.
 *
 * Lerps between minWidth and maxWidth, creating steps+1 widths.
 * Rounds to integers for consistent sprite generation.
 *
 * Args:
 *     zoom: Tree zoom configuration.
 *
 * Returns:
 *     Array of widths from smallest (horizon) to largest (foreground).
 */
export declare function calculateZoomWidths(zoom: TreeZoomConfig): readonly number[];
/**
 * Calculate sprite widths from layer config.
 *
 * Uses power curve for decreasing steps (fine at small end, coarse at large).
 *
 * Args:
 *     layerConfig: Layer sprite configuration.
 *
 * Returns:
 *     Array of widths from smallest to largest.
 */
export declare function calculateLayerWidths(layerConfig: LayerSpriteConfig): readonly number[];
/**
 * Get sprite widths from config for a sprite name.
 *
 * Priority order:
 * 1. Explicit widths array
 * 2. First animation's widths
 * 3. Layer config (auto-calculated)
 * 4. Zoom config (legacy)
 *
 * Args:
 *     config: Application config.
 *     spriteName: Name of sprite to get widths for.
 *
 * Returns:
 *     Sorted array of available widths (smallest to largest).
 *
 * Raises:
 *     Error: If sprite not found or has no widths defined.
 */
export declare function getSpriteWidths(config: Config, spriteName: string): readonly number[];
/**
 * Create layer instances from validated config.
 *
 * Instantiates entities based on layer configuration:
 * - If tile=true: tiles sprites across viewport with buffer
 * - If positions specified: creates entity at each position
 * - Otherwise: creates single centered entity
 *
 * Args:
 *     layers: Validated layer configurations.
 *     registry: Registry of loaded sprite frames.
 *     viewportWidth: Viewport width in characters.
 *
 * Returns:
 *     Array of layer instances with entities.
 *
 * Raises:
 *     Error: If sprite not found in registry.
 */
export declare function createLayerInstances(layers: readonly ValidatedLayer[], registry: SpriteRegistry, viewportWidth: number): LayerInstance[];
/** Test hooks for internal functions */
export declare const _test_hooks: {
    calculateZoomWidths: typeof calculateZoomWidths;
    calculateLayerWidths: typeof calculateLayerWidths;
    getSpriteWidths: typeof getSpriteWidths;
    createLayerInstances: typeof createLayerInstances;
};
//# sourceMappingURL=layers.d.ts.map