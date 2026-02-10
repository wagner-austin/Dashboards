/**
 * Generic scene sprite for simple static or animated background objects.
 */
import type { FrameSet } from "../types.js";
import type { SceneSpriteState, SceneState } from "../layers/types.js";
/**
 * Create initial state for a scene sprite.
 *
 * Args:
 *     spriteName: Identifier for sprite lookup.
 *     sizes: Available size variants.
 *     worldX: Initial world X position.
 *     worldZ: Initial world Z position (depth).
 *     sizeIdx: Initial size index.
 *
 * Returns:
 *     SceneSpriteState with provided values.
 */
export declare function createSceneSpriteState(spriteName: string, sizes: readonly FrameSet[], worldX: number, worldZ: number, sizeIdx: number): SceneSpriteState;
/**
 * Get current frame for scene sprite.
 *
 * Args:
 *     state: Scene sprite state.
 *
 * Returns:
 *     Frame data with lines and width, or null if invalid.
 */
export declare function getSceneSpriteFrame(state: SceneSpriteState): {
    lines: string[];
    width: number;
} | null;
/**
 * Advance animation frame (wraps around).
 *
 * Args:
 *     state: Scene sprite state to update.
 */
export declare function advanceSceneSpriteFrame(state: SceneSpriteState): void;
/**
 * Advance frame index for all scene sprites in all layers.
 *
 * Args:
 *     scene: Scene state containing all layers.
 */
export declare function advanceAllSceneSpriteFrames(scene: SceneState): void;
/**
 * Create callback for layer animation timer.
 *
 * Args:
 *     scene: Scene state to animate.
 *
 * Returns:
 *     Callback function that advances all sprite frames.
 */
export declare function createLayerAnimationCallback(scene: SceneState): () => void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createSceneSpriteState: typeof createSceneSpriteState;
    getSceneSpriteFrame: typeof getSceneSpriteFrame;
    advanceSceneSpriteFrame: typeof advanceSceneSpriteFrame;
    advanceAllSceneSpriteFrames: typeof advanceAllSceneSpriteFrames;
    createLayerAnimationCallback: typeof createLayerAnimationCallback;
};
//# sourceMappingURL=SceneSprite.d.ts.map