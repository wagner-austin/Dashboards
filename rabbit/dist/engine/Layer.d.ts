/**
 * Layer management - grouping sprites at the same depth.
 */
import type { Layer, Sprite } from "../types.js";
/** Create a new layer */
export declare function createLayer(name: string, parallax: number): Layer;
/** Add a sprite to a layer */
export declare function addSprite(layer: Layer, sprite: Sprite): void;
/** Remove a sprite from a layer */
export declare function removeSprite(layer: Layer, spriteName: string): void;
/** Update all sprites in a layer based on camera movement */
export declare function updateLayerPosition(layer: Layer, cameraX: number, _baseX: number): void;
/** Get all sprites in a layer */
export declare function getSprites(layer: Layer): readonly Sprite[];
//# sourceMappingURL=Layer.d.ts.map