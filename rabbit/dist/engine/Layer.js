/**
 * Layer management - grouping sprites at the same depth.
 */
/** Create a new layer */
export function createLayer(name, parallax) {
    return {
        name,
        parallax,
        sprites: [],
    };
}
/** Add a sprite to a layer */
export function addSprite(layer, sprite) {
    layer.sprites.push(sprite);
}
/** Remove a sprite from a layer */
export function removeSprite(layer, spriteName) {
    const index = layer.sprites.findIndex((s) => s.name === spriteName);
    if (index !== -1) {
        layer.sprites.splice(index, 1);
    }
}
/** Update all sprites in a layer based on camera movement */
export function updateLayerPosition(layer, cameraX, _baseX) {
    // Parallax: sprites further away move slower
    // parallax 0 = static (sky), parallax 1 = moves with player
    for (const sprite of layer.sprites) {
        // This is a simple offset based on camera - actual implementation
        // may need to track original positions
        sprite.x -= cameraX * layer.parallax;
    }
}
/** Get all sprites in a layer */
export function getSprites(layer) {
    return layer.sprites;
}
//# sourceMappingURL=Layer.js.map