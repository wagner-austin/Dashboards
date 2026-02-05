/**
 * Layer loading from config.
 * Dynamically loads sprite frames based on config.
 */
import type { Config, FrameSet } from "../types.js";
import type { ValidatedLayer, LayerInstance } from "../layers/types.js";
/** Registry of loaded sprite frames by name */
export interface SpriteRegistry {
    readonly sprites: ReadonlyMap<string, readonly FrameSet[]>;
}
/**
 * Get sprite widths from config for a sprite name.
 * Returns sorted array of available widths.
 */
export declare function getSpriteWidths(config: Config, spriteName: string): readonly number[];
/**
 * Create layer instances from validated config.
 * Instantiates entities at default positions.
 */
export declare function createLayerInstances(layers: readonly ValidatedLayer[], registry: SpriteRegistry, viewportWidth: number): LayerInstance[];
/** Test hooks for internal functions */
export declare const _test_hooks: {
    getSpriteWidths: typeof getSpriteWidths;
    createLayerInstances: typeof createLayerInstances;
};
//# sourceMappingURL=layers.d.ts.map