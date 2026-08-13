/**
 * Camera movement driven by the effective movement intent.
 *
 * Separate from any one input source: the camera integrates whatever intent
 * won arbitration, so keyboard, touch, and autopilot all scroll the world
 * identically.
 */
import type { InputState } from "./state.js";
/**
 * Move the camera through depth while the bunny is hopping.
 *
 * Hopping "toward" decreases Z (toward the viewer); "away" increases it.
 * Depth wraps at the configured bounds for an endless world.
 *
 * Args:
 *     state: Input state with bunny, camera, and depthBounds.
 *     deltaTime: Seconds since the previous frame.
 */
export declare function processDepthMovement(state: InputState, deltaTime: number): void;
/**
 * Move the camera horizontally while the bunny is moving under intent.
 *
 * Args:
 *     state: Input state with bunny, camera, and effective intent.
 *     deltaTime: Seconds since the previous frame.
 */
export declare function processHorizontalMovement(state: InputState, deltaTime: number): void;
/**
 * Return the camera to its starting position.
 *
 * Args:
 *     state: Input state whose camera is reset.
 */
export declare function resetCamera(state: InputState): void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    processDepthMovement: typeof processDepthMovement;
    processHorizontalMovement: typeof processHorizontalMovement;
    resetCamera: typeof resetCamera;
    CAMERA_Z_SPEED: number;
    CAMERA_X_SPEED: number;
};
//# sourceMappingURL=movement.d.ts.map