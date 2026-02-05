/**
 * Layer loading from config.
 * Dynamically loads sprite frames based on config.
 */
import { createSceneSpriteState } from "../entities/SceneSprite.js";
/**
 * Get sprite widths from config for a sprite name.
 * Returns sorted array of available widths.
 */
export function getSpriteWidths(config, spriteName) {
    const spriteConfig = config.sprites[spriteName];
    if (spriteConfig === undefined) {
        throw new Error(`Sprite "${spriteName}" not found in config`);
    }
    // Check for widths directly on sprite
    if (spriteConfig.widths !== undefined) {
        return [...spriteConfig.widths].sort((a, b) => a - b);
    }
    // Check for widths in first animation
    if (spriteConfig.animations !== undefined) {
        const animationKeys = Object.keys(spriteConfig.animations);
        const firstKey = animationKeys[0];
        if (firstKey !== undefined) {
            const firstAnim = spriteConfig.animations[firstKey];
            if (firstAnim !== undefined) {
                return [...firstAnim.widths].sort((a, b) => a - b);
            }
        }
    }
    throw new Error(`Sprite "${spriteName}" has no widths defined`);
}
/**
 * Create layer instances from validated config.
 * Instantiates entities at default positions.
 */
export function createLayerInstances(layers, registry, viewportWidth) {
    const instances = [];
    for (const config of layers) {
        const entities = [];
        for (const spriteName of config.spriteNames) {
            const sizes = registry.sprites.get(spriteName);
            if (sizes === undefined) {
                throw new Error(`Sprite "${spriteName}" not found in registry`);
            }
            const middleSizeIdx = Math.floor(sizes.length / 2);
            const spriteWidth = sizes[middleSizeIdx]?.width ?? 100;
            if (config.tile) {
                // Create multiple entities to tile across viewport (plus buffer for scrolling)
                const tileBuffer = viewportWidth * 4; // Extra width for parallax scrolling
                const totalWidth = viewportWidth + tileBuffer;
                const numTiles = Math.ceil(totalWidth / spriteWidth) + 1;
                const startX = -tileBuffer / 2;
                for (let i = 0; i < numTiles; i++) {
                    const x = startX + i * spriteWidth;
                    const entity = createSceneSpriteState(spriteName, sizes, x, middleSizeIdx);
                    entities.push(entity);
                }
            }
            else {
                // Create single entity centered in viewport
                const x = Math.floor(viewportWidth / 2);
                const entity = createSceneSpriteState(spriteName, sizes, x, middleSizeIdx);
                entities.push(entity);
            }
        }
        instances.push({ config, entities });
    }
    return instances;
}
/** Test hooks for internal functions */
export const _test_hooks = {
    getSpriteWidths,
    createLayerInstances,
};
//# sourceMappingURL=layers.js.map