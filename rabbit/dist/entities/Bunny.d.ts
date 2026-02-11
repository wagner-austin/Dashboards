/**
 * Bunny entity - state machine, animations, and frame selection.
 */
import { type AnimationTimer } from "../loaders/sprites.js";
/**
 * Animation state discriminated union.
 *
 * Each variant represents a distinct animation state with its required data.
 */
export type AnimationState = IdleState | WalkState | JumpState | HopState | TransitionState;
/** Bunny is standing still, idle animation looping. */
export interface IdleState {
    readonly kind: "idle";
    frameIdx: number;
}
/** Bunny is walking left or right. */
export interface WalkState {
    readonly kind: "walk";
    frameIdx: number;
}
/** Bunny is jumping, will return to previous state after. */
export interface JumpState {
    readonly kind: "jump";
    frameIdx: number;
    readonly returnTo: "idle" | "walk";
}
/** Bunny is hopping away or toward camera. */
export interface HopState {
    readonly kind: "hop";
    readonly direction: "away" | "toward";
    frameIdx: number;
    readonly returnTo: "idle" | "walk";
}
/** Bunny is transitioning between states. */
export interface TransitionState {
    readonly kind: "transition";
    readonly type: TransitionType;
    frameIdx: number;
    readonly pendingAction: PendingAction | null;
    readonly returnTo: "idle" | "walk";
}
/** Types of transitions. */
export type TransitionType = "idle_to_walk" | "walk_to_idle" | "walk_to_turn_away" | "walk_to_turn_toward";
/** Actions that can be pending during a transition. */
export type PendingAction = "walk" | "jump" | "hop_away" | "hop_toward";
/**
 * Bunny state containing animation and direction.
 */
export interface BunnyState {
    facingRight: boolean;
    animation: AnimationState;
}
/**
 * Bunny animation frames organized by animation type.
 */
export interface BunnyFrames {
    readonly walkLeft: readonly string[];
    readonly walkRight: readonly string[];
    readonly jumpLeft: readonly string[];
    readonly jumpRight: readonly string[];
    readonly idleLeft: readonly string[];
    readonly idleRight: readonly string[];
    readonly walkToIdleLeft: readonly string[];
    readonly walkToIdleRight: readonly string[];
    readonly walkToTurnAwayLeft: readonly string[];
    readonly walkToTurnAwayRight: readonly string[];
    readonly walkToTurnTowardLeft: readonly string[];
    readonly walkToTurnTowardRight: readonly string[];
    readonly hopAway: readonly string[];
    readonly hopToward: readonly string[];
}
/**
 * Animation timers for each animation type.
 */
export interface BunnyTimers {
    walk: AnimationTimer;
    idle: AnimationTimer;
    jump: AnimationTimer;
    transition: AnimationTimer;
    hop: AnimationTimer;
}
/**
 * Check if bunny is currently hopping.
 *
 * Args:
 *     state: Bunny state.
 *
 * Returns:
 *     True if animation is hop.
 */
export declare function isHopping(state: BunnyState): boolean;
/**
 * Check if bunny is currently jumping.
 *
 * Args:
 *     state: Bunny state.
 *
 * Returns:
 *     True if animation is jump.
 */
export declare function isJumping(state: BunnyState): boolean;
/**
 * Check if bunny is currently walking.
 *
 * Args:
 *     state: Bunny state.
 *
 * Returns:
 *     True if animation is walk.
 */
export declare function isWalking(state: BunnyState): boolean;
/**
 * Get hop direction if hopping, null otherwise.
 *
 * Args:
 *     state: Bunny state.
 *
 * Returns:
 *     "away" or "toward" if hopping, null otherwise.
 */
export declare function getHopDirection(state: BunnyState): "away" | "toward" | null;
/**
 * Create initial bunny state.
 *
 * Returns:
 *     BunnyState in idle animation facing left.
 */
export declare function createInitialBunnyState(): BunnyState;
/**
 * Create bunny animation timers.
 *
 * Args:
 *     state: Mutable bunny state.
 *     frames: Animation frame data.
 *     intervals: Timer intervals in milliseconds.
 *
 * Returns:
 *     BunnyTimers with all animation timers.
 */
export declare function createBunnyTimers(state: BunnyState, frames: BunnyFrames, intervals: {
    walk: number;
    idle: number;
    jump: number;
    transition: number;
    hop: number;
}): BunnyTimers;
/**
 * Get current bunny frame to render.
 *
 * Args:
 *     state: Bunny state.
 *     frames: Animation frame data.
 *
 * Returns:
 *     Object with frame lines and frame index.
 */
export declare function getBunnyFrame(state: BunnyState, frames: BunnyFrames): {
    lines: string[];
    frameIdx: number;
};
/** Test hooks for internal functions */
export declare const _test_hooks: {
    isHopping: typeof isHopping;
    isJumping: typeof isJumping;
    isWalking: typeof isWalking;
    getHopDirection: typeof getHopDirection;
};
//# sourceMappingURL=Bunny.d.ts.map