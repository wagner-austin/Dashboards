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
export function createSceneSpriteState(
  spriteName: string,
  sizes: FrameSet[],
  worldX: number,
  worldZ: number,
  sizeIdx: number
): SceneSpriteState {
  return {
    spriteName,
    sizes,
    sizeIdx,
    frameIdx: 0,
    worldX,
    worldZ,
  };
}

/**
 * Get current frame for scene sprite.
 *
 * Args:
 *     state: Scene sprite state.
 *
 * Returns:
 *     Frame data with lines and width, or null if invalid.
 */
export function getSceneSpriteFrame(
  state: SceneSpriteState
): { lines: string[]; width: number } | null {
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
 * Advance animation frame (wraps around).
 *
 * Args:
 *     state: Scene sprite state to update.
 */
export function advanceSceneSpriteFrame(state: SceneSpriteState): void {
  const currentSize = state.sizes[state.sizeIdx];
  if (currentSize === undefined) {
    return;
  }
  state.frameIdx = (state.frameIdx + 1) % currentSize.frames.length;
}

/**
 * Advance frame index for all scene sprites in all layers.
 *
 * Args:
 *     scene: Scene state containing all layers.
 */
export function advanceAllSceneSpriteFrames(scene: SceneState): void {
  for (const layer of scene.layers) {
    for (const entity of layer.entities) {
      advanceSceneSpriteFrame(entity);
    }
  }
}

/**
 * Create callback for layer animation timer.
 *
 * Args:
 *     scene: Scene state to animate.
 *
 * Returns:
 *     Callback function that advances all sprite frames.
 */
export function createLayerAnimationCallback(scene: SceneState): () => void {
  return () => {
    advanceAllSceneSpriteFrames(scene);
  };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  createSceneSpriteState,
  getSceneSpriteFrame,
  advanceSceneSpriteFrame,
  advanceAllSceneSpriteFrames,
  createLayerAnimationCallback,
};
