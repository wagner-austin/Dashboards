/**
 * Width generation for layer-based sprites.
 *
 * Generates sprite widths using a power curve formula that produces
 * fine steps for small sizes (distant) and coarse steps for large
 * sizes (close), matching natural perspective perception.
 */
/** Power exponent for width curve (>1 = fine steps at small end) */
const WIDTH_CURVE_POWER = 1.8;
/** Offset from largest size for default layer (third largest) */
const DEFAULT_SIZE_OFFSET = 2;
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
export function generateLayerWidths(config) {
    if (config.layerDepth < 1) {
        throw new Error("layerDepth must be at least 1");
    }
    if (config.minWidth >= config.maxWidth) {
        throw new Error("minWidth must be less than maxWidth");
    }
    const widths = [];
    const range = config.maxWidth - config.minWidth;
    const steps = config.layerDepth - 1;
    for (let i = 0; i < config.layerDepth; i++) {
        const t = steps > 0 ? i / steps : 0;
        const curved = Math.pow(t, WIDTH_CURVE_POWER);
        const width = Math.round(config.minWidth + range * curved);
        widths.push(width);
    }
    return widths;
}
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
export function layerToSizeIndex(currentLayer, defaultLayer, numSizes) {
    if (numSizes < 1) {
        return null;
    }
    // At default layer, show third largest (offset 2 from largest)
    const defaultSizeIdx = Math.max(0, numSizes - 1 - DEFAULT_SIZE_OFFSET);
    // Layer difference: negative = closer, positive = farther
    const layerDiff = currentLayer - defaultLayer;
    // Size index: higher layer = smaller size (lower index)
    const sizeIdx = defaultSizeIdx - layerDiff;
    // Check bounds
    if (sizeIdx < 0 || sizeIdx >= numSizes) {
        return null;
    }
    return sizeIdx;
}
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
export function isLayerVisible(currentLayer, defaultLayer, numSizes) {
    return layerToSizeIndex(currentLayer, defaultLayer, numSizes) !== null;
}
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
export function getVisibleLayerRange(defaultLayer, numSizes) {
    const defaultSizeIdx = Math.max(0, numSizes - 1 - DEFAULT_SIZE_OFFSET);
    // Min layer: when sizeIdx would be numSizes - 1 (largest)
    const minLayer = defaultLayer - (numSizes - 1 - defaultSizeIdx);
    // Max layer: when sizeIdx would be 0 (smallest)
    const maxLayer = defaultLayer + defaultSizeIdx;
    return { minLayer, maxLayer };
}
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
export function layerToWorldZ(layer) {
    // Layer 0 = Z 50 (very close), Layer 10 = Z 100 (reference), Layer 20 = Z 150
    return 50 + layer * 5;
}
/**
 * Convert world Z coordinate back to layer number.
 *
 * Args:
 *     worldZ: World Z coordinate.
 *
 * Returns:
 *     Layer number (may be fractional).
 */
export function worldZToLayer(worldZ) {
    return (worldZ - 50) / 5;
}
/** Test hooks for internal functions */
export const _test_hooks = {
    generateLayerWidths,
    layerToSizeIndex,
    isLayerVisible,
    getVisibleLayerRange,
    layerToWorldZ,
    worldZToLayer,
    WIDTH_CURVE_POWER,
    DEFAULT_SIZE_OFFSET,
};
//# sourceMappingURL=widths.js.map