/**
 * Keyboard input handling with unified input model.
 *
 * Uses raw input tracking (horizontalHeld, verticalHeld) that both keyboard
 * and touch inputs set. Movement processing interprets these based on bunny
 * animation state, ensuring consistent behavior across input methods.
 */
import { type BunnyState, type BunnyFrames, type BunnyTimers } from "../entities/Bunny.js";
import type { ViewportState } from "../rendering/Viewport.js";
import type { Camera, DepthBounds } from "../world/Projection.js";
import { isPendingJump, handleJumpInput, handleWalkKeyDown, handleWalkKeyUp, handleHopInput, handleHopRelease } from "./handlers.js";
/**
 * Horizontal input direction.
 */
export type HorizontalInput = "left" | "right" | null;
/**
 * Vertical input direction.
 */
export type VerticalInput = "up" | "down" | null;
/**
 * Input state containing all mutable game state.
 *
 * bunny: Bunny animation state.
 * viewport: Screen dimensions.
 * camera: Camera position.
 * depthBounds: Bounds for depth wrapping (from config).
 * horizontalHeld: Raw horizontal input (A/D or touch left/right).
 * verticalHeld: Raw vertical input (W/S or touch up/down).
 */
export interface InputState {
    bunny: BunnyState;
    viewport: ViewportState;
    camera: Camera;
    depthBounds: DepthBounds;
    horizontalHeld: HorizontalInput;
    verticalHeld: VerticalInput;
}
/**
 * Process input state change and trigger appropriate animations.
 *
 * Called when raw input changes (key press/release or touch direction change).
 * Compares previous and new input to determine which handlers to call.
 * This is the single source of truth for input-to-animation mapping.
 *
 * Args:
 *     prevHorizontal: Previous horizontal input.
 *     prevVertical: Previous vertical input.
 *     newHorizontal: New horizontal input.
 *     newVertical: New vertical input.
 *     state: Input state containing bunny.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 */
export declare function processInputChange(prevHorizontal: HorizontalInput, prevVertical: VerticalInput, newHorizontal: HorizontalInput, newVertical: VerticalInput, state: InputState, bunnyFrames: BunnyFrames, bunnyTimers: BunnyTimers): void;
/**
 * Setup keyboard controls for the game.
 *
 * Attaches keydown and keyup listeners that update raw input state
 * and call processInputChange for animation handling.
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
 * Camera moves when bunny is hopping, with infinite wrapping at depth bounds.
 * Moving "toward" decreases Z (toward viewer).
 * Moving "away" increases Z (into scene).
 *
 * Args:
 *     state: Input state with bunny, camera, and depthBounds.
 *     deltaTime: Time since last frame in seconds.
 */
export declare function processDepthMovement(state: InputState, deltaTime: number): void;
/**
 * Process horizontal camera movement.
 *
 * Camera moves horizontally when bunny is hopping or walking and
 * horizontal input is held. Uses same speed for both modes.
 *
 * Args:
 *     state: Input state with bunny, camera, and horizontalHeld.
 *     deltaTime: Time since last frame in seconds.
 */
export declare function processHorizontalMovement(state: InputState, deltaTime: number): void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    handleJumpInput: typeof handleJumpInput;
    handleWalkKeyDown: typeof handleWalkKeyDown;
    handleWalkKeyUp: typeof handleWalkKeyUp;
    handleHopInput: typeof handleHopInput;
    handleHopRelease: typeof handleHopRelease;
    isPendingJump: typeof isPendingJump;
    processInputChange: typeof processInputChange;
    processDepthMovement: typeof processDepthMovement;
    processHorizontalMovement: typeof processHorizontalMovement;
    CAMERA_Z_SPEED: number;
    CAMERA_X_SPEED: number;
};
//# sourceMappingURL=Keyboard.d.ts.map