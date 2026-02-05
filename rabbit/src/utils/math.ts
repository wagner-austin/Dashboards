/**
 * Math utilities for animations and transitions.
 */

/** Speed multiplier calculation for a given tree size index */
export function getSpeedMultiplier(treeSizeIdx: number): number {
  return 0.5 + treeSizeIdx * 0.5;
}

/** Ease-in-out S-curve for smooth transitions */
export function easeInOut(progress: number): number {
  return progress < 0.5
    ? 2 * progress * progress
    : 1 - Math.pow(-2 * progress + 2, 2) / 2;
}

/** Lerp between two values with optional easing */
export function lerp(start: number, end: number, progress: number, eased = true): number {
  const t = eased ? easeInOut(progress) : progress;
  return start + (end - start) * t;
}
