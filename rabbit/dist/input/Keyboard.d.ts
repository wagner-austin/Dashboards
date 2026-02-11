/**
 * Keyboard input handling.
 */
import { type BunnyState, type BunnyFrames, type BunnyTimers } from "../entities/Bunny.js";
import type { ViewportState } from "../rendering/Viewport.js";
import type { Camera } from "../world/Projection.js";
/**
 * Input state containing all mutable game state.
 *
 * bunny: Bunny animation state.
 * viewport: Screen dimensions.
 * camera: Camera position.
 * hopKeyHeld: Whether W/S key is currently held (for depth movement).
 * slideKeyHeld: Whether A/D key is currently held (for horizontal slide during hop).
 */
export interface InputState {
    bunny: BunnyState;
    viewport: ViewportState;
    camera: Camera;
    hopKeyHeld: "away" | "toward" | null;
    slideKeyHeld: "left" | "right" | null;
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
 * Process camera depth movement based on hop state.
 *
 * Camera only moves when bunny is actually hopping, not during transitions.
 *
 * Args:
 *     state: Input state with bunny and camera.
 */
export declare function processDepthMovement(state: InputState): void;
/**
 * Process horizontal camera movement when sliding during hop.
 *
 * Camera only moves horizontally when bunny is hopping and A/D is held.
 *
 * Args:
 *     state: Input state with bunny, camera, and slideKeyHeld.
 */
export declare function processHorizontalMovement(state: InputState): void;
/**
 * Check if bunny has a pending jump.
 *
 * Args:
 *     bunny: Bunny state.
 *
 * Returns:
 *     True if in transition with pending jump action.
 */
declare function isPendingJump(bunny: BunnyState): boolean;
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
/**
 * Handle hop input (W/S key pressed).
 *
 * Starts the animation sequence for hopping into depth (away) or out (toward).
 * From idle: idle → walk_to_turn → hop (loop)
 * From walk: walk → walk_to_turn → hop (loop)
 *
 * Args:
 *     bunny: Bunny state to update.
 *     timers: Bunny animation timers.
 *     direction: "away" for W key, "toward" for S key.
 */
declare function handleHopInput(bunny: BunnyState, timers: BunnyTimers, direction: "away" | "toward"): void;
/**
 * Handle hop release (W/S key released).
 *
 * Stops the hopping animation and transitions back to previous state.
 * If released during transition, cancels and returns to previous state.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     timers: Bunny animation timers.
 */
declare function handleHopRelease(bunny: BunnyState, timers: BunnyTimers): void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    handleJumpInput: typeof handleJumpInput;
    handleWalkInput: typeof handleWalkInput;
    handleHopInput: typeof handleHopInput;
    handleHopRelease: typeof handleHopRelease;
    processDepthMovement: typeof processDepthMovement;
    processHorizontalMovement: typeof processHorizontalMovement;
    isPendingJump: typeof isPendingJump;
    CAMERA_Z_SPEED: number;
    MIN_CAMERA_Z: number;
    MAX_CAMERA_Z: number;
    CAMERA_X_SPEED: number;
};
export {};
//# sourceMappingURL=Keyboard.d.ts.map