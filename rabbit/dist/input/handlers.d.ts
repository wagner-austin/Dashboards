/**
 * Shared input handlers for keyboard and touch.
 *
 * These handlers process input actions and mutate bunny animation state.
 * Both keyboard and touch input sources use these same handlers to ensure
 * consistent behavior and a single source of truth.
 */
import { type BunnyState, type BunnyFrames, type BunnyTimers, type IsHorizontalHeld } from "../entities/Bunny.js";
/**
 * Check if bunny has a pending jump.
 *
 * Args:
 *     bunny: Bunny state.
 *
 * Returns:
 *     True if in transition with pending jump action.
 */
export declare function isPendingJump(bunny: BunnyState): boolean;
/**
 * Handle jump input.
 *
 * Transitions bunny to jump animation from various states:
 * - From idle: starts transition with pending jump
 * - From walk: immediate jump
 * - From transition: interrupt and jump
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 */
export declare function handleJumpInput(bunny: BunnyState, frames: BunnyFrames, timers: BunnyTimers): void;
/**
 * Handle walk key down (start walking).
 *
 * Starts walking animation in the specified direction.
 * If already walking in a different direction, switches direction.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 *     goingRight: Direction of movement.
 */
export declare function handleWalkKeyDown(bunny: BunnyState, frames: BunnyFrames, timers: BunnyTimers, goingRight: boolean): void;
/**
 * Handle walk key up (stop walking).
 *
 * Transitions from walking to idle when the walk key is released.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     timers: Bunny animation timers.
 */
export declare function handleWalkKeyUp(bunny: BunnyState, timers: BunnyTimers): void;
/**
 * Handle hop input (W/S key or touch up/down).
 *
 * Starts the animation sequence for hopping into depth (away) or out (toward).
 * From idle: idle -> walk_to_turn -> hop (loop)
 * From walk: walk -> walk_to_turn -> hop (loop)
 * From transition: updates pending action
 *
 * Does nothing if already jumping or hopping.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     timers: Bunny animation timers.
 *     direction: "away" for up/W, "toward" for down/S.
 */
export declare function handleHopInput(bunny: BunnyState, timers: BunnyTimers, direction: "away" | "toward"): void;
/**
 * Handle hop release (W/S key or touch released).
 *
 * Stops the hopping animation and checks current input to decide next state.
 * If released during transition, cancels and checks current input.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     timers: Bunny animation timers.
 *     isHorizontalHeld: Callback to check current horizontal input.
 */
export declare function handleHopRelease(bunny: BunnyState, timers: BunnyTimers, isHorizontalHeld: IsHorizontalHeld): void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    isPendingJump: typeof isPendingJump;
    handleJumpInput: typeof handleJumpInput;
    handleWalkKeyDown: typeof handleWalkKeyDown;
    handleWalkKeyUp: typeof handleWalkKeyUp;
    handleHopInput: typeof handleHopInput;
    handleHopRelease: typeof handleHopRelease;
};
//# sourceMappingURL=handlers.d.ts.map