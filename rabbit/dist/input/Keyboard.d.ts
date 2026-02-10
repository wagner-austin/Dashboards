/**
 * Keyboard input handling.
 */
import type { BunnyState, BunnyFrames, BunnyTimers } from "../entities/Bunny.js";
import type { ViewportState } from "../rendering/Viewport.js";
import type { Camera } from "../world/Projection.js";
/**
 * Input state containing all mutable game state.
 *
 * bunny: Bunny animation state.
 * viewport: Screen dimensions.
 * camera: Camera position.
 * zoomDirection: Current zoom direction (1=in, -1=out, 0=none).
 */
export interface InputState {
    bunny: BunnyState;
    viewport: ViewportState;
    camera: Camera;
    zoomDirection: number;
}
/**
 * Setup keyboard controls for the game.
 *
 * Args:
 *     state: Mutable input state.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 */
export declare function setupKeyboardControls(state: InputState, bunnyFrames: BunnyFrames, bunnyTimers: BunnyTimers): void;
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
export declare function processZoom(state: InputState): void;
/**
 * Handle jump input.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 */
declare function handleJumpInput(bunny: BunnyState, frames: BunnyFrames, timers: BunnyTimers): void;
/**
 * Handle walk input.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 *     goingRight: Direction of movement.
 */
declare function handleWalkInput(bunny: BunnyState, frames: BunnyFrames, timers: BunnyTimers, goingRight: boolean): void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    handleJumpInput: typeof handleJumpInput;
    handleWalkInput: typeof handleWalkInput;
    processZoom: typeof processZoom;
    CAMERA_Z_SPEED: number;
    MIN_CAMERA_Z: number;
    MAX_CAMERA_Z: number;
};
export {};
//# sourceMappingURL=Keyboard.d.ts.map