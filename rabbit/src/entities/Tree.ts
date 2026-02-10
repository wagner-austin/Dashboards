/**
 * Tree entity - state, zoom, and frame selection.
 */

import { createAnimationTimer, type AnimationTimer } from "../loaders/sprites.js";
import { createTransitionState, type EntityTransitionState } from "./EntityTransition.js";

/** Tree X position as fraction of viewport width (negative = left of center). */
export const TREE_X_RATIO = -1 / 8;

/**
 * Tree size variant with frames.
 *
 * width: Sprite width in characters.
 * frames: Animation frames for this size.
 */
export interface TreeSize {
  readonly width: number;
  readonly frames: readonly string[];
}

/**
 * Tree entity state.
 *
 * Extends EntityTransitionState for size/visibility transitions.
 * sizeIdx represents zoom level (0=horizon/smallest, max=foreground/largest).
 *
 * frameIdx: Current animation frame.
 * direction: Animation direction (1=forward, -1=backward).
 * worldX: World X position for scrolling.
 */
export interface TreeState extends EntityTransitionState {
  frameIdx: number;
  direction: number;
  worldX: number;
}

/**
 * Create initial tree state.
 *
 * Starts at second-largest visible size. The last size is the fade-out size,
 * so we use sizeCount - 3 to start one step back from the largest visible.
 *
 * Args:
 *     viewportWidth: Viewport width for initial positioning.
 *     sizeCount: Number of available tree sizes (including fade-out size).
 *
 * Returns:
 *     TreeState with initial values.
 */
export function createInitialTreeState(viewportWidth: number, sizeCount = 3): TreeState {
  const initialSizeIdx = Math.max(0, sizeCount - 3);
  return {
    ...createTransitionState(initialSizeIdx),
    frameIdx: 0,
    direction: 1,
    worldX: viewportWidth * TREE_X_RATIO,
  };
}

/**
 * Create animation timer for tree.
 *
 * Args:
 *     state: Tree state to animate.
 *     sizes: Available tree sizes.
 *     intervalMs: Animation interval in milliseconds.
 *
 * Returns:
 *     AnimationTimer for ping-pong animation.
 */
export function createTreeTimer(
  state: TreeState,
  sizes: TreeSize[],
  intervalMs: number
): AnimationTimer {
  return createAnimationTimer(intervalMs, () => {
    const currentSize = sizes[state.sizeIdx];
    if (currentSize === undefined) {
      return;
    }
    const frameCount = currentSize.frames.length;
    state.frameIdx += state.direction;
    if (state.frameIdx >= frameCount) {
      state.frameIdx = frameCount - 2;
      state.direction = -1;
    } else if (state.frameIdx < 0) {
      state.frameIdx = 1;
      state.direction = 1;
    }
  });
}

/**
 * Get current tree frame.
 *
 * Args:
 *     state: Tree state.
 *     sizes: Available tree sizes.
 *
 * Returns:
 *     Frame data with lines and width, or null if invalid.
 */
export function getTreeFrame(
  state: TreeState,
  sizes: TreeSize[]
): { lines: string[]; width: number } | null {
  const currentSize = sizes[state.sizeIdx];
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
 * Get frames for size transition animation.
 *
 * Args:
 *     state: Tree state.
 *     sizes: Available tree sizes.
 *
 * Returns:
 *     Current and target frames with target index, or null if invalid.
 */
export function getTreeTransitionFrames(
  state: TreeState,
  sizes: TreeSize[]
): {
  current: { lines: string[]; width: number };
  target: { lines: string[]; width: number };
  targetIdx: number;
} | null {
  const currentSize = sizes[state.sizeIdx];
  if (currentSize === undefined) {
    return null;
  }

  const targetIdx =
    state.sizeIdx < state.targetSizeIdx
      ? state.sizeIdx + 1
      : state.sizeIdx - 1;
  const targetSize = sizes[targetIdx];
  if (targetSize === undefined) {
    return null;
  }

  const currentFrame = currentSize.frames[state.frameIdx];
  const targetFrame = targetSize.frames[state.frameIdx % targetSize.frames.length];
  if (currentFrame === undefined || targetFrame === undefined) {
    return null;
  }

  return {
    current: { lines: currentFrame.split("\n"), width: currentSize.width },
    target: { lines: targetFrame.split("\n"), width: targetSize.width },
    targetIdx,
  };
}
