/**
 * Bunny entity - state machine, animations, and frame selection.
 */

import { createAnimationTimer, type AnimationTimer } from "../loaders/sprites.js";

/**
 * Animation state discriminated union.
 *
 * Each variant represents a distinct animation state with its required data.
 */
export type AnimationState =
  | IdleState
  | WalkState
  | JumpState
  | HopState
  | TransitionState;

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
export type TransitionType =
  | "idle_to_walk"
  | "walk_to_idle"
  | "walk_to_turn_away"
  | "walk_to_turn_toward";

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
export function isHopping(state: BunnyState): boolean {
  return state.animation.kind === "hop";
}

/**
 * Check if bunny is currently jumping.
 *
 * Args:
 *     state: Bunny state.
 *
 * Returns:
 *     True if animation is jump.
 */
export function isJumping(state: BunnyState): boolean {
  return state.animation.kind === "jump";
}

/**
 * Check if bunny is currently walking.
 *
 * Args:
 *     state: Bunny state.
 *
 * Returns:
 *     True if animation is walk.
 */
export function isWalking(state: BunnyState): boolean {
  return state.animation.kind === "walk";
}

/**
 * Get hop direction if hopping, null otherwise.
 *
 * Args:
 *     state: Bunny state.
 *
 * Returns:
 *     "away" or "toward" if hopping, null otherwise.
 */
export function getHopDirection(state: BunnyState): "away" | "toward" | null {
  if (state.animation.kind === "hop") {
    return state.animation.direction;
  }
  return null;
}

/**
 * Create initial bunny state.
 *
 * Returns:
 *     BunnyState in idle animation facing left.
 */
export function createInitialBunnyState(): BunnyState {
  return {
    facingRight: false,
    animation: { kind: "idle", frameIdx: 0 },
  };
}

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
export function createBunnyTimers(
  state: BunnyState,
  frames: BunnyFrames,
  intervals: { walk: number; idle: number; jump: number; transition: number; hop: number }
): BunnyTimers {
  const walkTimer = createAnimationTimer(intervals.walk, () => {
    if (state.animation.kind !== "walk") return;
    const walkFrames = state.facingRight ? frames.walkRight : frames.walkLeft;
    state.animation.frameIdx = (state.animation.frameIdx + 1) % walkFrames.length;
  });

  const idleTimer = createAnimationTimer(intervals.idle, () => {
    if (state.animation.kind !== "idle") return;
    const idleFrames = state.facingRight ? frames.idleRight : frames.idleLeft;
    state.animation.frameIdx = (state.animation.frameIdx + 1) % idleFrames.length;
  });

  const jumpTimer = createAnimationTimer(intervals.jump, () => {
    if (state.animation.kind !== "jump") return;
    const jumpFrames = state.facingRight ? frames.jumpRight : frames.jumpLeft;
    state.animation.frameIdx++;

    if (state.animation.frameIdx >= jumpFrames.length) {
      jumpTimer.stop();
      const returnTo = state.animation.returnTo;

      if (returnTo === "walk") {
        state.animation = { kind: "walk", frameIdx: 0 };
        walkTimer.start();
      } else {
        state.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" };
        transitionTimer.start();
      }
    }
  });

  const transitionTimer = createAnimationTimer(intervals.transition, () => {
    if (state.animation.kind !== "transition") return;

    const anim = state.animation;

    if (anim.type === "walk_to_idle") {
      const transitionFrames = state.facingRight ? frames.walkToIdleRight : frames.walkToIdleLeft;
      anim.frameIdx++;

      if (anim.frameIdx >= transitionFrames.length) {
        transitionTimer.stop();
        state.animation = { kind: "idle", frameIdx: 0 };
        idleTimer.start();
      }
    } else if (anim.type === "idle_to_walk") {
      anim.frameIdx--;

      if (anim.frameIdx < 0) {
        transitionTimer.stop();

        if (anim.pendingAction === "jump") {
          state.animation = { kind: "jump", frameIdx: 0, returnTo: "idle" };
          jumpTimer.start();
        } else if (anim.pendingAction === "hop_away") {
          state.animation = { kind: "transition", type: "walk_to_turn_away", frameIdx: 0, pendingAction: null, returnTo: anim.returnTo };
          transitionTimer.start();
        } else if (anim.pendingAction === "hop_toward") {
          state.animation = { kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: anim.returnTo };
          transitionTimer.start();
        } else {
          state.animation = { kind: "walk", frameIdx: 0 };
          walkTimer.start();
        }
      }
    } else if (anim.type === "walk_to_turn_away") {
      anim.frameIdx++;
      const turnAwayFrames = state.facingRight ? frames.walkToTurnAwayRight : frames.walkToTurnAwayLeft;

      if (anim.frameIdx >= turnAwayFrames.length) {
        transitionTimer.stop();
        state.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: anim.returnTo };
        hopTimer.start();
      }
    } else {
      // walk_to_turn_toward
      anim.frameIdx++;
      const turnTowardFrames = state.facingRight ? frames.walkToTurnTowardRight : frames.walkToTurnTowardLeft;

      if (anim.frameIdx >= turnTowardFrames.length) {
        transitionTimer.stop();
        state.animation = { kind: "hop", direction: "toward", frameIdx: 0, returnTo: anim.returnTo };
        hopTimer.start();
      }
    }
  });

  const hopTimer = createAnimationTimer(intervals.hop, () => {
    if (state.animation.kind !== "hop") return;
    const hopFrames = state.animation.direction === "away" ? frames.hopAway : frames.hopToward;
    state.animation.frameIdx = (state.animation.frameIdx + 1) % hopFrames.length;
  });

  return { walk: walkTimer, idle: idleTimer, jump: jumpTimer, transition: transitionTimer, hop: hopTimer };
}

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
export function getBunnyFrame(state: BunnyState, frames: BunnyFrames): { lines: string[]; frameIdx: number } {
  const anim = state.animation;
  let bunnyFrames: readonly string[];
  let frameIdx: number;

  switch (anim.kind) {
    case "idle":
      bunnyFrames = state.facingRight ? frames.idleRight : frames.idleLeft;
      frameIdx = anim.frameIdx % bunnyFrames.length;
      break;
    case "walk":
      bunnyFrames = state.facingRight ? frames.walkRight : frames.walkLeft;
      frameIdx = anim.frameIdx;
      break;
    case "jump":
      bunnyFrames = state.facingRight ? frames.jumpRight : frames.jumpLeft;
      frameIdx = anim.frameIdx;
      break;
    case "hop":
      bunnyFrames = anim.direction === "away" ? frames.hopAway : frames.hopToward;
      frameIdx = anim.frameIdx % bunnyFrames.length;
      break;
    case "transition":
      if (anim.type === "idle_to_walk" || anim.type === "walk_to_idle") {
        bunnyFrames = state.facingRight ? frames.walkToIdleRight : frames.walkToIdleLeft;
      } else if (anim.type === "walk_to_turn_away") {
        bunnyFrames = state.facingRight ? frames.walkToTurnAwayRight : frames.walkToTurnAwayLeft;
      } else {
        bunnyFrames = state.facingRight ? frames.walkToTurnTowardRight : frames.walkToTurnTowardLeft;
      }
      frameIdx = Math.max(0, Math.min(anim.frameIdx, bunnyFrames.length - 1));
      break;
  }

  const frame = bunnyFrames[frameIdx];
  const lines = frame !== undefined ? frame.split("\n") : [];
  return { lines, frameIdx };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  isHopping,
  isJumping,
  isWalking,
  getHopDirection,
};
