/**
 * Layer management - grouping sprites at the same depth.
 */

import type { Layer, Sprite } from "../types.js";

/** Create a new layer */
export function createLayer(name: string, parallax: number): Layer {
  return {
    name,
    parallax,
    sprites: [],
  };
}

/** Add a sprite to a layer */
export function addSprite(layer: Layer, sprite: Sprite): void {
  layer.sprites.push(sprite);
}

/** Remove a sprite from a layer */
export function removeSprite(layer: Layer, spriteName: string): void {
  const index = layer.sprites.findIndex((s) => s.name === spriteName);
  if (index !== -1) {
    layer.sprites.splice(index, 1);
  }
}

/** Update all sprites in a layer based on camera movement */
export function updateLayerPosition(
  layer: Layer,
  cameraX: number,
  _baseX: number
): void {
  // Parallax: sprites further away move slower
  // parallax 0 = static (sky), parallax 1 = moves with player
  for (const sprite of layer.sprites) {
    // This is a simple offset based on camera - actual implementation
    // may need to track original positions
    sprite.x -= cameraX * layer.parallax;
  }
}

/** Get all sprites in a layer */
export function getSprites(layer: Layer): readonly Sprite[] {
  return layer.sprites;
}
