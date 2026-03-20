/**
 * Width generation for layer-based sprites.
 *
 * Generates sprite widths using a power curve formula that produces
 * fine steps for small sizes (distant) and coarse steps for large
 * sizes (close), matching natural perspective perception.
 */
import type { LayerSpriteConfig } from "../types.js";
/**
 * Generate sprite widths from layer config using power curve.
 *
 * Uses formula: width[i] = min + (max - min) * (i / (n-1))^power
 * This produces smaller increments for small widths (distant objects)
 * and larger increments for large widths (close objects).
 *
 * Args:
 *     config: Layer sprite configuration with min/max width and layer depth.
 *
 * Returns:
 *     Array of widths from smallest to largest, length equals layerDepth.
 *
 * Raises:
 *     Error: If layerDepth < 1 or minWidth >= maxWidth.
 */
export declare function generateLayerWidths(config: LayerSpriteConfig): readonly number[];
/**
 * Calculate size index for a given layer number.
 *
 * At defaultLayer, returns third largest size (numSizes - 3).
 * Lower layer numbers = larger sizes (closer).
 * Higher layer numbers = smaller sizes (farther).
 *
 * Args:
 *     currentLayer: The layer number being rendered.
 *     defaultLayer: The sprite's configured default layer.
 *     numSizes: Total number of available sizes.
 *
 * Returns:
 *     Size index (0 = smallest, numSizes-1 = largest), or null if out of range.
 */
export declare function layerToSizeIndex(currentLayer: number, defaultLayer: number, numSizes: number): number | null;
/**
 * Check if a layer is in the visible range for a sprite.
 *
 * Args:
 *     currentLayer: The layer number being checked.
 *     defaultLayer: The sprite's configured default layer.
 *     numSizes: Total number of available sizes.
 *
 * Returns:
 *     True if the sprite is visible at this layer.
 */
export declare function isLayerVisible(currentLayer: number, defaultLayer: number, numSizes: number): boolean;
/**
 * Get the layer range where a sprite is visible.
 *
 * Args:
 *     defaultLayer: The sprite's configured default layer.
 *     numSizes: Total number of available sizes.
 *
 * Returns:
 *     Object with minLayer and maxLayer (inclusive).
 */
export declare function getVisibleLayerRange(defaultLayer: number, numSizes: number): {
    readonly minLayer: number;
    readonly maxLayer: number;
};
/**
 * Convert layer number to world Z coordinate for projection.
 *
 * Higher layer numbers map to higher Z values (farther from camera).
 * Uses linear scaling with a base offset.
 *
 * Args:
 *     layer: Layer number.
 *
 * Returns:
 *     World Z coordinate.
 */
export declare function layerToWorldZ(layer: number): number;
/**
 * Convert world Z coordinate back to layer number.
 *
 * Args:
 *     worldZ: World Z coordinate.
 *
 * Returns:
 *     Layer number (may be fractional).
 */
export declare function worldZToLayer(worldZ: number): number;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    generateLayerWidths: typeof generateLayerWidths;
    layerToSizeIndex: typeof layerToSizeIndex;
    isLayerVisible: typeof isLayerVisible;
    getVisibleLayerRange: typeof getVisibleLayerRange;
    layerToWorldZ: typeof layerToWorldZ;
    worldZToLayer: typeof worldZToLayer;
    WIDTH_CURVE_POWER: number;
    DEFAULT_SIZE_OFFSET: number;
};
//# sourceMappingURL=widths.d.ts.map