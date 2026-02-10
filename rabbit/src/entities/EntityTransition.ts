/**
 * Generic entity transition system for size changes and visibility fading.
 *
 * Provides reusable transition logic for projected scene entities (trees, rocks, etc).
 */

/**
 * Transition state that any entity can include.
 *
 * sizeIdx: Current size index.
 * targetSizeIdx: Target size for transitions.
 * sizeTransitionProgress: Transition progress (0-1).
 * sizeTransitionDirection: Direction of current transition (1=growing, -1=shrinking, 0=none).
 * visibilityProgress: Fade progress (1=visible, 0=hidden).
 */
export interface EntityTransitionState {
  sizeIdx: number;
  targetSizeIdx: number;
  sizeTransitionProgress: number;
  sizeTransitionDirection: number;
  visibilityProgress: number;
}

/**
 * Create initial transition state.
 *
 * Args:
 *     sizeIdx: Initial size index.
 *
 * Returns:
 *     EntityTransitionState with initial values.
 */
export function createTransitionState(sizeIdx: number): EntityTransitionState {
  return {
    sizeIdx,
    targetSizeIdx: sizeIdx,
    sizeTransitionProgress: 0,
    sizeTransitionDirection: 0,
    visibilityProgress: 1,
  };
}

/**
 * Update size transition progress.
 *
 * Handles mid-transition direction changes by reversing progress.
 * Transitions move one step at a time toward the target.
 *
 * Args:
 *     state: Transition state to update.
 *     deltaTimeMs: Time since last frame in milliseconds.
 *     transitionDurationMs: Duration for one size step transition.
 *
 * Returns:
 *     Whether entity is currently transitioning.
 */
export function updateSizeTransition(
  state: EntityTransitionState,
  deltaTimeMs: number,
  transitionDurationMs: number
): boolean {
  if (state.sizeIdx === state.targetSizeIdx) {
    state.sizeTransitionProgress = 0;
    state.sizeTransitionDirection = 0;
    return false;
  }

  // Determine desired direction
  const desiredDirection = state.sizeIdx < state.targetSizeIdx ? 1 : -1;

  // If direction changed mid-transition, reverse progress
  if (state.sizeTransitionDirection !== 0 && state.sizeTransitionDirection !== desiredDirection) {
    state.sizeTransitionProgress = 1 - state.sizeTransitionProgress;
  }
  state.sizeTransitionDirection = desiredDirection;

  state.sizeTransitionProgress += deltaTimeMs / transitionDurationMs;

  if (state.sizeTransitionProgress >= 1) {
    state.sizeIdx += desiredDirection;
    state.sizeTransitionProgress = 0;
  }

  return true;
}

/**
 * Update visibility fade progress.
 *
 * Smoothly fades entity in when becoming visible, out when becoming invisible.
 *
 * Args:
 *     state: Transition state to update.
 *     isVisible: Whether entity is currently in visible range.
 *     deltaTimeMs: Time since last frame in milliseconds.
 *     fadeDurationMs: Fade in/out duration.
 */
export function updateVisibilityFade(
  state: EntityTransitionState,
  isVisible: boolean,
  deltaTimeMs: number,
  fadeDurationMs: number
): void {
  const fadeStep = deltaTimeMs / fadeDurationMs;

  if (isVisible) {
    state.visibilityProgress = Math.min(1, state.visibilityProgress + fadeStep);
  } else {
    state.visibilityProgress = Math.max(0, state.visibilityProgress - fadeStep);
  }
}

/**
 * Check if entity should be drawn (visible or fading out).
 *
 * Args:
 *     state: Transition state to check.
 *
 * Returns:
 *     Whether entity should be rendered.
 */
export function shouldDrawEntity(state: EntityTransitionState): boolean {
  return state.visibilityProgress > 0;
}

/**
 * Check if entity is currently transitioning between sizes.
 *
 * Args:
 *     state: Transition state to check.
 *
 * Returns:
 *     Whether entity is mid-transition.
 */
export function isTransitioning(state: EntityTransitionState): boolean {
  return state.sizeIdx !== state.targetSizeIdx || state.sizeTransitionProgress > 0;
}

/**
 * Check if entity should be drawn in the foreground (in front of bunny).
 *
 * An entity is in foreground when at its largest size (closest to camera).
 * This includes when transitioning TO the max size, so the layer change
 * happens at the start of the transition rather than the end.
 *
 * Args:
 *     state: Transition state to check.
 *     sizeCount: Total number of available sizes for this entity.
 *
 * Returns:
 *     Whether entity should be drawn in foreground layer.
 */
export function isEntityInForeground(
  state: EntityTransitionState,
  sizeCount: number
): boolean {
  if (sizeCount <= 1) {
    return false;
  }
  // Foreground when at the two largest sizes (largest visible + fade-out size)
  const foregroundThreshold = sizeCount - 2;
  return state.sizeIdx >= foregroundThreshold;
}

/** Test hooks for internal functions */
export const _test_hooks = {
  createTransitionState,
  updateSizeTransition,
  updateVisibilityFade,
  shouldDrawEntity,
  isTransitioning,
  isEntityInForeground,
};
