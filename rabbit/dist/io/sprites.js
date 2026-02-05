/**
 * Sprite loading I/O code.
 * This module contains dynamic imports which require browser/bundler integration.
 * Excluded from unit test coverage - testability ensured through dependency injection.
 */
import { _test_hooks as spritesHooks } from "../loaders/sprites.js";
const { validateSpriteModule } = spritesHooks;
/** Dynamic import with validation */
async function importSpriteModule(path) {
    const module = await import(/* @vite-ignore */ path);
    return validateSpriteModule(module, path);
}
/**
 * Load sprite frames for animated sprites (with direction).
 */
export async function loadSpriteFrames(spriteName, animationName, width, direction) {
    const suffix = direction !== undefined ? `_${direction}` : "";
    const path = `../sprites/${spriteName}/${animationName}/w${String(width)}${suffix}.js`;
    const module = await importSpriteModule(path);
    return {
        width,
        frames: module.frames,
    };
}
/**
 * Load sprite frames for static sprites (no direction).
 */
export async function loadStaticSpriteFrames(spriteName, width) {
    const path = `../sprites/${spriteName}/w${String(width)}.js`;
    const module = await importSpriteModule(path);
    return {
        width,
        frames: module.frames,
    };
}
/**
 * Load config from JSON file.
 */
export async function loadConfig() {
    const { validateConfig } = spritesHooks;
    const response = await fetch("./config.json");
    const data = await response.json();
    return validateConfig(data);
}
/**
 * Load all bunny animation frames.
 */
export async function loadBunnyFrames(_config) {
    const [walkLeft, walkRight, jumpLeft, jumpRight, idleLeft, idleRight, walkToIdleLeft, walkToIdleRight] = await Promise.all([
        loadSpriteFrames("bunny", "walk", 50, "left"),
        loadSpriteFrames("bunny", "walk", 50, "right"),
        loadSpriteFrames("bunny", "jump", 50, "left"),
        loadSpriteFrames("bunny", "jump", 50, "right"),
        loadSpriteFrames("bunny", "idle", 40, "left"),
        loadSpriteFrames("bunny", "idle", 40, "right"),
        loadSpriteFrames("bunny", "walk_to_idle", 40, "left"),
        loadSpriteFrames("bunny", "walk_to_idle", 40, "right"),
    ]);
    return {
        walkLeft: walkLeft.frames,
        walkRight: walkRight.frames,
        jumpLeft: jumpLeft.frames,
        jumpRight: jumpRight.frames,
        idleLeft: idleLeft.frames,
        idleRight: idleRight.frames,
        walkToIdleLeft: walkToIdleLeft.frames,
        walkToIdleRight: walkToIdleRight.frames,
    };
}
/**
 * Load all tree size variations.
 */
export async function loadTreeSizes(_config) {
    const widths = [60, 120, 180];
    const sizes = [];
    for (const w of widths) {
        const set = await loadStaticSpriteFrames("tree", w);
        sizes.push({ width: w, frames: set.frames });
    }
    return sizes;
}
/**
 * Load all sprites referenced by layers.
 */
export async function loadLayerSprites(config, layers) {
    const { getSpriteWidths } = await import("../loaders/layers.js");
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
//# sourceMappingURL=sprites.js.map