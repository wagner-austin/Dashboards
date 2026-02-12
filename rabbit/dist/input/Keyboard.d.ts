/**
 * Keyboard input handling.
 */
import { type BunnyState, type BunnyFrames, type BunnyTimers } from "../entities/Bunny.js";
import type { ViewportState } from "../rendering/Viewport.js";
import type { Camera, DepthBounds } from "../world/Projection.js";
import { isPendingJump, handleJumpInput, handleWalkKeyDown, handleWalkKeyUp, handleHopInput, handleHopRelease } from "./handlers.js";
/**
 * Input state containing all mutable game state.
 *
 * bunny: Bunny animation state.
 * viewport: Screen dimensions.
 * camera: Camera position.
 * depthBounds: Bounds for depth wrapping (from config).
 * hopKeyHeld: Whether W/S key is currently held (for depth movement).
 * slideKeyHeld: Whether A/D key is currently held (for horizontal slide during hop).
 * walkKeyHeld: Whether A/D key is currently held (for horizontal walk movement).
 */
export interface InputState {
    bunny: BunnyState;
    viewport: ViewportState;
    camera: Camera;
    depthBounds: DepthBounds;
    hopKeyHeld: "away" | "toward" | null;
    slideKeyHeld: "left" | "right" | null;
    walkKeyHeld: "left" | "right" | null;
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
 * Camera moves when bunny is hopping, with infinite wrapping at depth bounds.
 * Moving "toward" decreases Z (toward viewer).
 * Moving "away" increases Z (into scene).
 *
 * Args:
 *     state: Input state with bunny, camera, and depthBounds.
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
 * Process horizontal camera movement while walking.
 *
 * Camera moves horizontally when bunny is walking and walkKeyHeld is set.
 *
 * Args:
 *     state: Input state with bunny, camera, and walkKeyHeld.
 */
export declare function processWalkMovement(state: InputState): void;
/** Test hooks for internal functions (re-exports handlers + local constants) */
export declare const _test_hooks: {
    handleJumpInput: typeof handleJumpInput;
    handleWalkKeyDown: typeof handleWalkKeyDown;
    handleWalkKeyUp: typeof handleWalkKeyUp;
    handleHopInput: typeof handleHopInput;
    handleHopRelease: typeof handleHopRelease;
    isPendingJump: typeof isPendingJump;
    processDepthMovement: typeof processDepthMovement;
    processHorizontalMovement: typeof processHorizontalMovement;
    processWalkMovement: typeof processWalkMovement;
    CAMERA_Z_SPEED: number;
    CAMERA_X_SPEED: number;
    WALK_SPEED: number;
};
//# sourceMappingURL=Keyboard.d.ts.map