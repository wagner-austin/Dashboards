/**
 * Keyboard input handling.
 */
import { DEFAULT_CAMERA_Z } from "../world/Projection.js";
/**
 * Setup keyboard controls for the game.
 *
 * Args:
 *     state: Mutable input state.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 */
export function setupKeyboardControls(state, bunnyFrames, bunnyTimers) {
    document.addEventListener("keydown", (e) => {
        if (e.repeat) {
            return;
        }
        const key = e.key.toLowerCase();
        const isLeftKey = e.key === "ArrowLeft" || key === "a";
        const isRightKey = e.key === "ArrowRight" || key === "d";
        if (isLeftKey) {
            handleWalkInput(state.bunny, bunnyFrames, bunnyTimers, false);
        }
        else if (isRightKey) {
            handleWalkInput(state.bunny, bunnyFrames, bunnyTimers, true);
        }
        else if (e.key === " " && !state.bunny.isJumping && !state.bunny.pendingJump) {
            handleJumpInput(state.bunny, bunnyFrames, bunnyTimers);
            e.preventDefault();
        }
        else if (key === "r") {
            // Reset scene: camera position and zoom level
            state.camera = { x: 0, z: DEFAULT_CAMERA_Z };
        }
        else if (key === "w" || e.key === "ArrowUp") {
            // Set zoom direction to forward (into scene)
            state.zoomDirection = 1;
        }
        else if (key === "s" || e.key === "ArrowDown") {
            // Set zoom direction to backward (out of scene)
            state.zoomDirection = -1;
        }
    });
    document.addEventListener("keyup", (e) => {
        const key = e.key.toLowerCase();
        if (key === "w" || e.key === "ArrowUp" || key === "s" || e.key === "ArrowDown") {
            state.zoomDirection = 0;
        }
    });
}
/** Camera Z movement speed per frame */
const CAMERA_Z_SPEED = 0.5;
/** Minimum camera Z (closest to scene) */
const MIN_CAMERA_Z = 40;
/** Maximum camera Z (farthest from scene) */
const MAX_CAMERA_Z = 80;
/**
 * Process zoom based on held key direction.
 *
 * Moves camera forward/backward through the scene.
 * W/ArrowUp zooms in (moves camera forward, decreases z).
 * S/ArrowDown zooms out (moves camera backward, increases z).
 * All layer entities automatically resize via 3D projection.
 *
 * Args:
 *     state: Input state with zoomDirection and camera.
 */
export function processZoom(state) {
    if (state.zoomDirection === 0) {
        return;
    }
    let newZ = state.camera.z;
    if (state.zoomDirection === 1) {
        // Zoom in: move camera forward (decrease z)
        newZ = Math.max(state.camera.z - CAMERA_Z_SPEED, MIN_CAMERA_Z);
    }
    else if (state.zoomDirection === -1) {
        // Zoom out: move camera backward (increase z)
        newZ = Math.min(state.camera.z + CAMERA_Z_SPEED, MAX_CAMERA_Z);
    }
    state.camera = { ...state.camera, z: newZ };
}
/**
 * Handle jump input.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 */
function handleJumpInput(bunny, frames, timers) {
    const wasIdle = bunny.currentAnimation === "idle";
    const wasWalking = bunny.currentAnimation === "walk";
    if (wasIdle) {
        bunny.preJumpAnimation = "idle";
        bunny.pendingJump = true;
        timers.idle.stop();
        const transitionFrames = bunny.facingRight
            ? frames.walkToIdleRight
            : frames.walkToIdleLeft;
        bunny.currentAnimation = "idle_to_walk";
        bunny.bunnyFrameIdx = transitionFrames.length - 1;
        timers.transition.start();
    }
    else if (wasWalking) {
        bunny.preJumpAnimation = "walk";
        bunny.isJumping = true;
        bunny.jumpFrameIdx = 0;
        timers.walk.stop();
        timers.jump.start();
    }
    else {
        bunny.preJumpAnimation = bunny.isWalking ? "walk" : "idle";
        bunny.isJumping = true;
        bunny.jumpFrameIdx = 0;
        timers.transition.stop();
        timers.jump.start();
    }
}
/**
 * Handle walk input.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 *     goingRight: Direction of movement.
 */
function handleWalkInput(bunny, frames, timers, goingRight) {
    const sameDirection = bunny.facingRight === goingRight;
    if (bunny.isWalking && sameDirection && bunny.currentAnimation === "walk") {
        bunny.isWalking = false;
        timers.walk.stop();
        bunny.currentAnimation = "walk_to_idle";
        bunny.bunnyFrameIdx = 0;
        timers.transition.start();
    }
    else {
        const wasIdle = bunny.currentAnimation === "idle";
        const wasInTransition = bunny.currentAnimation === "walk_to_idle" ||
            bunny.currentAnimation === "idle_to_walk";
        bunny.facingRight = goingRight;
        bunny.isWalking = true;
        if (wasIdle) {
            timers.idle.stop();
            const transitionFrames = goingRight
                ? frames.walkToIdleRight
                : frames.walkToIdleLeft;
            bunny.currentAnimation = "idle_to_walk";
            bunny.bunnyFrameIdx = transitionFrames.length - 1;
            timers.transition.start();
        }
        else {
            if (wasInTransition) {
                timers.transition.stop();
            }
            bunny.currentAnimation = "walk";
            bunny.bunnyFrameIdx = 0;
            timers.walk.start();
        }
    }
}
/** Test hooks for internal functions */
export const _test_hooks = {
    handleJumpInput,
    handleWalkInput,
    processZoom,
    CAMERA_Z_SPEED,
    MIN_CAMERA_Z,
    MAX_CAMERA_Z,
};
//# sourceMappingURL=Keyboard.js.map