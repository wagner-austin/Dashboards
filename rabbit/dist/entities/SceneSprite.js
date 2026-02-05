/**
 * Generic scene sprite for simple static or animated background objects.
 */
import { GROUND_TILE } from "../rendering/Ground.js";
/**
 * Create initial state for a scene sprite.
 */
export function createSceneSpriteState(spriteName, sizes, x, sizeIdx) {
    return {
        spriteName,
        sizes,
        sizeIdx,
        frameIdx: 0,
        x,
    };
}
/**
 * Get current frame for scene sprite.
 * Returns null if size or frame index is invalid.
 */
export function getSceneSpriteFrame(state) {
    const currentSize = state.sizes[state.sizeIdx];
    if (currentSize === undefined) {
        return null;
    }
    const frame = currentSize.frames[state.frameIdx];
    if (frame === undefined) {
        return null;
    }
    return {
        lines: frame.split("\n"),
        width: currentSize.width,
    };
}
/**
 * Calculate Y position for scene sprite (bottom-aligned to ground).
 */
export function calculateSceneSpriteY(state, viewportHeight) {
    const frame = getSceneSpriteFrame(state);
    if (frame === null) {
        return viewportHeight - GROUND_TILE.length;
    }
    const spriteHeight = frame.lines.length;
    return viewportHeight - GROUND_TILE.length - spriteHeight;
}
/**
 * Advance animation frame (wraps around).
 */
export function advanceSceneSpriteFrame(state) {
    const currentSize = state.sizes[state.sizeIdx];
    if (currentSize === undefined) {
        return;
    }
    state.frameIdx = (state.frameIdx + 1) % currentSize.frames.length;
}
/**
 * Advance frame index for all scene sprites in all layers.
 */
export function advanceAllSceneSpriteFrames(scene) {
    for (const layer of scene.layers) {
        for (const entity of layer.entities) {
            advanceSceneSpriteFrame(entity);
        }
    }
}
/**
 * Create callback for layer animation timer.
 */
export function createLayerAnimationCallback(scene) {
    return () => {
        advanceAllSceneSpriteFrames(scene);
    };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    createSceneSpriteState,
    getSceneSpriteFrame,
    calculateSceneSpriteY,
    advanceSceneSpriteFrame,
    advanceAllSceneSpriteFrames,
    createLayerAnimationCallback,
};
//# sourceMappingURL=SceneSprite.js.map