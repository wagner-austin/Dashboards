/**
 * Parallax scrolling calculations.
 * Pure functions for calculating scroll positions and speed transitions.
 */

import { getSpeedMultiplier, lerp } from "../state/types.js";

/** Result of a scroll update */
export interface ScrollUpdate {
  readonly groundScrollX: number;
  readonly treeCenterX: number;
}

/** Result of a speed transition update */
export interface SpeedTransitionUpdate {
  readonly treeSizeIdx: number;
  readonly treeSizeTransitionProgress: number;
  readonly currentSpeedMultiplier: number;
}

/** Calculate new scroll positions */
export function calculateScrollUpdate(
  groundScrollX: number,
  treeCenterX: number,
  scrollAmount: number,
  facingRight: boolean,
  viewportWidth: number,
  maxTreeWidth: number
): ScrollUpdate {
  let newGroundX = groundScrollX;
  let newTreeX = treeCenterX;

  if (facingRight) {
    newGroundX -= scrollAmount;
    newTreeX -= scrollAmount;
    if (newTreeX < -maxTreeWidth / 2) {
      newTreeX = viewportWidth + maxTreeWidth / 2;
    }
  } else {
    newGroundX += scrollAmount;
    newTreeX += scrollAmount;
    if (newTreeX > viewportWidth + maxTreeWidth / 2) {
      newTreeX = -maxTreeWidth / 2;
    }
  }

  return {
    groundScrollX: newGroundX,
    treeCenterX: newTreeX,
  };
}

/** Update speed transition state */
export function updateSpeedTransition(
  treeSizeIdx: number,
  treeTargetSizeIdx: number,
  treeSizeTransitionProgress: number,
  deltaTimeMs: number,
  transitionDurationMs: number
): SpeedTransitionUpdate {
  const isTransitioning = treeSizeIdx !== treeTargetSizeIdx;

  if (!isTransitioning) {
    return {
      treeSizeIdx,
      treeSizeTransitionProgress: 0,
      currentSpeedMultiplier: getSpeedMultiplier(treeSizeIdx),
    };
  }

  const newProgress = treeSizeTransitionProgress + deltaTimeMs / transitionDurationMs;

  if (newProgress >= 1) {
    // Transition complete, move to next size
    const newSizeIdx = treeSizeIdx < treeTargetSizeIdx
      ? treeSizeIdx + 1
      : treeSizeIdx - 1;
    return {
      treeSizeIdx: newSizeIdx,
      treeSizeTransitionProgress: 0,
      currentSpeedMultiplier: getSpeedMultiplier(newSizeIdx),
    };
  }

  // Still transitioning, lerp the speed
  const currentMultiplier = getSpeedMultiplier(treeSizeIdx);
  const targetIdx = treeSizeIdx < treeTargetSizeIdx
    ? treeSizeIdx + 1
    : treeSizeIdx - 1;
  const targetMultiplier = getSpeedMultiplier(targetIdx);

  return {
    treeSizeIdx,
    treeSizeTransitionProgress: newProgress,
    currentSpeedMultiplier: lerp(currentMultiplier, targetMultiplier, newProgress),
  };
}
