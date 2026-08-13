/**
 * Camera movement driven by the effective movement intent.
 *
 * This is the only place the camera moves. Rendering used to pan it as well,
 * which meant two writers adding their speeds together and only one of them
 * being configurable; now `settings.scrollSpeed` really is the pan speed.
 *
 * Separate from any one input source: the camera integrates whatever intent
 * won arbitration, so keyboard, touch, and autopilot all scroll identically.
 */
import type { InputState } from "./state.js";
/**
 * Camera speeds, in world units per second.
 *
 * horizontal: Pan speed while walking, hopping, or airborne.
 * depth: Depth speed while hopping.
 */
export interface CameraSpeeds {
    readonly horizontal: number;
    readonly depth: number;
}
/**
 * Move the camera through depth while the bunny is hopping.
 *
 * Hopping "toward" decreases Z (toward the viewer); "away" increases it.
 * Depth wraps at the configured bounds for an endless world.
 *
 * Args:
 *     state: Input state with bunny, camera, and depthBounds.
 *     deltaTime: Seconds since the previous frame.
 *     speed: Depth speed in world units per second.
 */
export declare function processDepthMovement(state: InputState, deltaTime: number, speed: number): void;
/**
 * Move the camera horizontally while the bunny is moving under intent.
 *
 * Jumping counts as moving, so a jump taken mid-stride carries forward
 * instead of stopping the world in mid-air.
 *
 * Args:
 *     state: Input state with bunny, camera, and effective intent.
 *     deltaTime: Seconds since the previous frame.
 *     speed: Pan speed in world units per second.
 */
export declare function processHorizontalMovement(state: InputState, deltaTime: number, speed: number): void;
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
};
//# sourceMappingURL=movement.d.ts.map