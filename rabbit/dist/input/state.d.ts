/**
 * Shared mutable engine state read and written by the input layer.
 *
 * The `intent` field is the effective movement intent for the current frame.
 * It has exactly one writer, the input arbiter; every other module treats it
 * as read-only. Keeping it a single immutable value (rather than two loose
 * mutable fields) means a source cannot leave the axes in a half-updated
 * state between the mutation and the animation reducer running.
 */
import type { BunnyState } from "../entities/Bunny.js";
import type { ViewportState } from "../rendering/Viewport.js";
import type { Camera, DepthBounds } from "../world/Projection.js";
import { type MovementIntent } from "./intent.js";
/**
 * Input-layer view of engine state.
 *
 * bunny: Bunny animation state.
 * viewport: Screen dimensions.
 * camera: Camera position.
 * depthBounds: Bounds for depth wrapping (derived from config).
 * intent: Effective movement intent. Written only by the input arbiter.
 */
export interface InputState {
    bunny: BunnyState;
    viewport: ViewportState;
    camera: Camera;
    depthBounds: DepthBounds;
    intent: MovementIntent;
}
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
export declare function createInputState(bunny: BunnyState, viewport: ViewportState, camera: Camera, depthBounds: DepthBounds): InputState;
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
export declare function isHorizontalRequested(state: InputState): boolean;
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
export declare function createHorizontalHeldProbe(state: InputState): () => boolean;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createInputState: typeof createInputState;
    isHorizontalRequested: typeof isHorizontalRequested;
    createHorizontalHeldProbe: typeof createHorizontalHeldProbe;
};
//# sourceMappingURL=state.d.ts.map