/**
 * Generic scene sprite for simple static or animated background objects.
 */
import type { FrameSet } from "../types.js";
import type { SceneSpriteState, SceneState } from "../layers/types.js";
/**
 * Create initial state for a scene sprite.
 */
export declare function createSceneSpriteState(spriteName: string, sizes: readonly FrameSet[], x: number, sizeIdx: number): SceneSpriteState;
/**
 * Get current frame for scene sprite.
 * Returns null if size or frame index is invalid.
 */
export declare function getSceneSpriteFrame(state: SceneSpriteState): {
    lines: string[];
    width: number;
} | null;
/**
 * Calculate Y position for scene sprite (bottom-aligned to ground).
 */
export declare function calculateSceneSpriteY(state: SceneSpriteState, viewportHeight: number): number;
/**
 * Advance animation frame (wraps around).
 */
export declare function advanceSceneSpriteFrame(state: SceneSpriteState): void;
/**
 * Advance frame index for all scene sprites in all layers.
 */
export declare function advanceAllSceneSpriteFrames(scene: SceneState): void;
/**
 * Create callback for layer animation timer.
 */
export declare function createLayerAnimationCallback(scene: SceneState): () => void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createSceneSpriteState: typeof createSceneSpriteState;
    getSceneSpriteFrame: typeof getSceneSpriteFrame;
    calculateSceneSpriteY: typeof calculateSceneSpriteY;
    advanceSceneSpriteFrame: typeof advanceSceneSpriteFrame;
    advanceAllSceneSpriteFrames: typeof advanceAllSceneSpriteFrames;
    createLayerAnimationCallback: typeof createLayerAnimationCallback;
};
//# sourceMappingURL=SceneSprite.d.ts.map