/**
 * Camera movement driven by the effective movement intent.
 *
 * Separate from any one input source: the camera integrates whatever intent
 * won arbitration, so keyboard, touch, and autopilot all scroll the world
 * identically.
 */
import { DEFAULT_CAMERA_Z, wrapDepth } from "../world/Projection.js";
/** Camera Z movement speed per second. */
const CAMERA_Z_SPEED = 30;
/** Camera X movement speed per second. */
const CAMERA_X_SPEED = 120;
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
export function processDepthMovement(state, deltaTime) {
    const anim = state.bunny.animation;
    if (anim.kind !== "hop") {
        return;
    }
    const delta = anim.direction === "toward" ? -CAMERA_Z_SPEED : CAMERA_Z_SPEED;
    const newZ = wrapDepth(state.camera.z + delta * deltaTime, state.depthBounds.minZ, state.depthBounds.maxZ);
    state.camera = { ...state.camera, z: newZ };
}
/**
 * Move the camera horizontally while the bunny is moving under intent.
 *
 * Args:
 *     state: Input state with bunny, camera, and effective intent.
 *     deltaTime: Seconds since the previous frame.
 */
export function processHorizontalMovement(state, deltaTime) {
    const anim = state.bunny.animation;
    const isMoving = anim.kind === "hop" || anim.kind === "walk" || anim.kind === "jump";
    const horizontal = state.intent.horizontal;
    if (!isMoving || horizontal === null) {
        return;
    }
    const direction = horizontal === "left" ? -1 : 1;
    state.camera = { ...state.camera, x: state.camera.x + CAMERA_X_SPEED * deltaTime * direction };
}
/**
 * Return the camera to its starting position.
 *
 * Args:
 *     state: Input state whose camera is reset.
 */
export function resetCamera(state) {
    state.camera = { x: 0, z: DEFAULT_CAMERA_Z };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    processDepthMovement,
    processHorizontalMovement,
    resetCamera,
    CAMERA_Z_SPEED,
    CAMERA_X_SPEED,
};
//# sourceMappingURL=movement.js.map