/**
 * Progressive sprite loading for scene population.
 *
 * Loads sprites in a controlled order to populate scene progressively:
 * 1. Ground (instant - pure ASCII)
 * 2. Grass sprites
 * 3. Bunny animation frames
 * 4. Trees from smallest to largest width
 */
/**
 * Create empty mutable sprite registry.
 *
 * Args:
 *     spriteNames: Names of sprites to create entries for.
 *
 * Returns:
 *     MutableSpriteRegistry with empty arrays for each sprite.
 */
export function createMutableSpriteRegistry(spriteNames) {
    const sprites = new Map();
    for (const name of spriteNames) {
        sprites.set(name, []);
    }
    return { sprites };
}
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
export function getOrCreateSpriteArray(registry, spriteName) {
    const existing = registry.sprites.get(spriteName);
    if (existing !== undefined) {
        return existing;
    }
    const newArray = [];
    registry.sprites.set(spriteName, newArray);
    return newArray;
}
/**
 * Insert frame set into sorted position by width.
 *
 * Maintains ascending width order in the array.
 *
 * Args:
 *     sizes: Mutable array of frame sets.
 *     frameSet: Frame set to insert.
 */
export function insertSortedByWidth(sizes, frameSet) {
    let insertIdx = 0;
    for (let i = 0; i < sizes.length; i++) {
        const current = sizes[i];
        if (current !== undefined && current.width < frameSet.width) {
            insertIdx = i + 1;
        }
        else {
            break;
        }
    }
    sizes.splice(insertIdx, 0, frameSet);
}
/**
 * Collect all tree widths from config, sorted ascending (smallest first).
 *
 * Combines widths from all tree sprites and returns unique widths
 * with their sprite names, sorted by width ascending.
 *
 * Args:
 *     config: Application config with sprite definitions.
 *     treeNames: Names of tree sprites to collect widths from.
 *
 * Returns:
 *     Array of TreeWidthEntry sorted by width ascending.
 */
export function collectTreeWidths(config, treeNames) {
    const entries = [];
    for (const spriteName of treeNames) {
        const spriteConfig = config.sprites[spriteName];
        if (spriteConfig === undefined) {
            continue;
        }
        const widths = spriteConfig.widths;
        if (widths === undefined) {
            continue;
        }
        for (const width of widths) {
            entries.push({ spriteName, width });
        }
    }
    // Sort by width ascending (smallest first)
    entries.sort((a, b) => a.width - b.width);
    return entries;
}
/**
 * Get grass sprite names from config layers.
 *
 * Args:
 *     config: Application config with layer definitions.
 *
 * Returns:
 *     Array of grass sprite names.
 */
export function getGrassSpriteNames(config) {
    const grassNames = [];
    for (const layer of config.layers) {
        if (layer.sprites !== undefined) {
            for (const spriteName of layer.sprites) {
                if (spriteName.includes("grass")) {
                    grassNames.push(spriteName);
                }
            }
        }
    }
    return grassNames;
}
/**
 * Get tree sprite names from autoLayers config.
 *
 * Args:
 *     config: Application config with autoLayers.
 *
 * Returns:
 *     Array of tree sprite names, or empty if no autoLayers.
 */
export function getTreeSpriteNames(config) {
    if (config.autoLayers === undefined) {
        return [];
    }
    return config.autoLayers.sprites;
}
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
export function getSpriteWidthsFromConfig(config, spriteName) {
    const spriteConfig = config.sprites[spriteName];
    if (spriteConfig === undefined) {
        return [];
    }
    return spriteConfig.widths ?? [];
}
/** Test hooks for internal functions. */
export const _test_hooks = {
    createMutableSpriteRegistry,
    getOrCreateSpriteArray,
    insertSortedByWidth,
    collectTreeWidths,
    getGrassSpriteNames,
    getTreeSpriteNames,
    getSpriteWidthsFromConfig,
};
//# sourceMappingURL=progressive.js.map