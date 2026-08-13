/**
 * Shared mutable engine state read and written by the input layer.
 *
 * The `intent` field is the effective movement intent for the current frame.
 * It has exactly one writer, the input arbiter; every other module treats it
 * as read-only. Keeping it a single immutable value (rather than two loose
 * mutable fields) means a source cannot leave the axes in a half-updated
 * state between the mutation and the animation reducer running.
 */
import { NEUTRAL_INTENT } from "./intent.js";
/**
 * Create input state with a neutral starting intent.
 *
 * Args:
 *     bunny: Bunny animation state.
 *     viewport: Screen dimensions.
 *     camera: Starting camera position.
 *     depthBounds: Bounds for depth wrapping.
 *
 * Returns:
 *     InputState with no movement requested.
 */
export function createInputState(bunny, viewport, camera, depthBounds) {
    return { bunny, viewport, camera, depthBounds, intent: NEUTRAL_INTENT };
}
/**
 * Check whether the effective intent currently requests horizontal movement.
 *
 * Passed to the bunny timers so animation completion knows whether to settle
 * into idle or resume walking.
 *
 * Args:
 *     state: Input state to inspect.
 *
 * Returns:
 *     True if a horizontal direction is requested.
 */
export function isHorizontalRequested(state) {
    return state.intent.horizontal !== null;
}
/**
 * Build the callback the bunny timers use to decide how an animation settles.
 *
 * Bound to the effective intent rather than to any one source, so a walk that
 * the autopilot started resumes correctly after a jump just as a walk the user
 * started would.
 *
 * Args:
 *     state: Input state to probe.
 *
 * Returns:
 *     Callback reporting whether horizontal movement is currently requested.
 */
export function createHorizontalHeldProbe(state) {
    return () => isHorizontalRequested(state);
}
/** Test hooks for internal functions */
export const _test_hooks = {
    createInputState,
    isHorizontalRequested,
    createHorizontalHeldProbe,
};
//# sourceMappingURL=state.js.map