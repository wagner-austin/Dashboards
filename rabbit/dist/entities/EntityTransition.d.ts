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
export declare function createTransitionState(sizeIdx: number): EntityTransitionState;
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
export declare function updateSizeTransition(state: EntityTransitionState, deltaTimeMs: number, transitionDurationMs: number): boolean;
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
export declare function updateVisibilityFade(state: EntityTransitionState, isVisible: boolean, deltaTimeMs: number, fadeDurationMs: number): void;
/**
 * Check if entity should be drawn (visible or fading out).
 *
 * Args:
 *     state: Transition state to check.
 *
 * Returns:
 *     Whether entity should be rendered.
 */
export declare function shouldDrawEntity(state: EntityTransitionState): boolean;
/**
 * Check if entity is currently transitioning between sizes.
 *
 * Args:
 *     state: Transition state to check.
 *
 * Returns:
 *     Whether entity is mid-transition.
 */
export declare function isTransitioning(state: EntityTransitionState): boolean;
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
export declare function isEntityInForeground(state: EntityTransitionState, sizeCount: number): boolean;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createTransitionState: typeof createTransitionState;
    updateSizeTransition: typeof updateSizeTransition;
    updateVisibilityFade: typeof updateVisibilityFade;
    shouldDrawEntity: typeof shouldDrawEntity;
    isTransitioning: typeof isTransitioning;
    isEntityInForeground: typeof isEntityInForeground;
};
//# sourceMappingURL=EntityTransition.d.ts.map