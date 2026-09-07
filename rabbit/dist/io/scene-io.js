/**
 * Loading the scenery: trees, grass, and whatever else a layer names.
 *
 * Distinct from character-io.ts because scenery is loaded by width across
 * many sprites and reported progressively, while a character is loaded once
 * as a fixed set of animations. They share only the transport underneath.
 */
import { getSpriteWidths } from "../loaders/layers.js";
import { collectTreeWidths, getGrassSpriteNames, getTreeSpriteNames, getSpriteWidthsFromConfig, getOrCreateSpriteArray, insertSortedByWidth, } from "../loaders/progressive.js";
import { loadStaticSpriteFrames } from "./transport.js";
/**
 * Load all tree size variations from config.
 *
 * Reads tree sprite widths from config and loads each size.
 * Returns sizes sorted smallest to largest.
 *
 * Args:
 *     config: Application config with sprite definitions.
 *
 * Returns:
 *     Array of TreeSize sorted by width ascending.
 */
export async function loadTreeSizes(config) {
    const widths = getSpriteWidths(config, "tree1");
    const sizes = [];
    for (const w of widths) {
        const set = await loadStaticSpriteFrames("tree1", w);
        sizes.push({ width: w, frames: set.frames });
    }
    return sizes;
}
/**
 * Load all sprites referenced by layers.
 *
 * Args:
 *     config: Application config.
 *     layers: Validated layers naming the sprites to load.
 *
 * Returns:
 *     A registry holding each named sprite at every width it declares.
 */
export async function loadLayerSprites(config, layers) {
    const sprites = new Map();
    // Collect unique sprite names from all layers
    const spriteNames = new Set();
    for (const layer of layers) {
        for (const name of layer.spriteNames) {
            spriteNames.add(name);
        }
    }
    // Load each sprite's frames at all widths
    for (const name of spriteNames) {
        const widths = getSpriteWidths(config, name);
        const sizes = [];
        for (const width of widths) {
            const frameSet = await loadStaticSpriteFrames(name, width);
            sizes.push(frameSet);
        }
        sprites.set(name, sizes);
    }
    return { sprites };
}
/**
 * Load grass sprites into mutable registry.
 *
 * Args:
 *     config: Application config.
 *     registry: Mutable sprite registry.
 *     onProgress: Progress callback.
 */
export async function loadGrassSprites(config, registry, onProgress) {
    const grassNames = getGrassSpriteNames(config);
    let current = 0;
    let total = 0;
    // Count total widths to load
    for (const name of grassNames) {
        const widths = getSpriteWidthsFromConfig(config, name);
        total += widths.length;
    }
    for (const name of grassNames) {
        const widths = getSpriteWidthsFromConfig(config, name);
        const sizes = getOrCreateSpriteArray(registry, name);
        for (const width of widths) {
            current++;
            onProgress({ phase: "grass", current, total, spriteName: name, width });
            const frameSet = await loadStaticSpriteFrames(name, width);
            insertSortedByWidth(sizes, frameSet);
        }
    }
}
/**
 * Load tree sprites progressively from smallest to largest.
 *
 * Loads trees interleaved across tree types (tree1, tree2, etc.)
 * so that the smallest trees from all types load first.
 *
 * Args:
 *     config: Application config.
 *     registry: Mutable sprite registry.
 *     onProgress: Progress callback.
 */
export async function loadTreeSpritesProgressive(config, registry, onProgress) {
    const treeNames = getTreeSpriteNames(config);
    const entries = collectTreeWidths(config, treeNames);
    const total = entries.length;
    // Iterated by value rather than by index: indexing under
    // noUncheckedIndexedAccess forces an `undefined` arm that cannot happen,
    // since the list being indexed is the one just built above.
    let current = 0;
    for (const { spriteName, width } of entries) {
        current++;
        onProgress({ phase: "trees", current, total, spriteName, width });
        const sizes = getOrCreateSpriteArray(registry, spriteName);
        const frameSet = await loadStaticSpriteFrames(spriteName, width);
        insertSortedByWidth(sizes, frameSet);
    }
}
//# sourceMappingURL=scene-io.js.map