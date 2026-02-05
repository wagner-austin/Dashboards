/**
 * Bunny entity - state, animations, and frame selection.
 */

import { createAnimationTimer, type AnimationTimer } from "../loaders/sprites.js";

export type BunnyAnimation = "walk" | "jump" | "idle" | "walk_to_idle" | "idle_to_walk";

export interface BunnyState {
  facingRight: boolean;
  currentAnimation: BunnyAnimation;
  bunnyFrameIdx: number;
  isJumping: boolean;
  jumpFrameIdx: number;
  isWalking: boolean;
}

export interface BunnyFrames {
  walkLeft: readonly string[];
  walkRight: readonly string[];
  jumpLeft: readonly string[];
  jumpRight: readonly string[];
  idleLeft: readonly string[];
  idleRight: readonly string[];
  walkToIdleLeft: readonly string[];
  walkToIdleRight: readonly string[];
}

export interface BunnyTimers {
  walk: AnimationTimer;
  idle: AnimationTimer;
  jump: AnimationTimer;
  transition: AnimationTimer;
}

export function createInitialBunnyState(): BunnyState {
  return {
    facingRight: false,
    currentAnimation: "idle",
    bunnyFrameIdx: 0,
    isJumping: false,
    jumpFrameIdx: 0,
    isWalking: false,
  };
}

export function createBunnyTimers(
  state: BunnyState,
  frames: BunnyFrames,
  intervals: { walk: number; idle: number; jump: number; transition: number }
): BunnyTimers {
  const walkTimer = createAnimationTimer(intervals.walk, () => {
    if (!state.isJumping && state.currentAnimation === "walk") {
      const walkFrames = state.facingRight ? frames.walkRight : frames.walkLeft;
      state.bunnyFrameIdx = (state.bunnyFrameIdx + 1) % walkFrames.length;
    }
  });

  const idleTimer = createAnimationTimer(intervals.idle, () => {
    if (!state.isJumping && state.currentAnimation === "idle") {
      const idleFrames = state.facingRight ? frames.idleRight : frames.idleLeft;
      state.bunnyFrameIdx = (state.bunnyFrameIdx + 1) % idleFrames.length;
    }
  });

  const jumpTimer = createAnimationTimer(intervals.jump, () => {
    const jumpFrames = state.facingRight ? frames.jumpRight : frames.jumpLeft;
    state.jumpFrameIdx++;
    if (state.jumpFrameIdx >= jumpFrames.length) {
      state.isJumping = false;
      state.jumpFrameIdx = 0;
      jumpTimer.stop();
    }
  });

  const transitionTimer = createAnimationTimer(intervals.transition, () => {
    if (state.isJumping) return;

    const transitionFrames = state.facingRight
      ? frames.walkToIdleRight
      : frames.walkToIdleLeft;

    if (state.currentAnimation === "walk_to_idle") {
      state.bunnyFrameIdx++;
      if (state.bunnyFrameIdx >= transitionFrames.length) {
        state.currentAnimation = "idle";
        state.bunnyFrameIdx = 0;
        transitionTimer.stop();
        idleTimer.start();
      }
    } else if (state.currentAnimation === "idle_to_walk") {
      state.bunnyFrameIdx--;
      if (state.bunnyFrameIdx < 0) {
        state.currentAnimation = "walk";
        state.bunnyFrameIdx = 0;
        transitionTimer.stop();
        walkTimer.start();
      }
    }
  });

  return { walk: walkTimer, idle: idleTimer, jump: jumpTimer, transition: transitionTimer };
}

export function getBunnyFrame(state: BunnyState, frames: BunnyFrames): { lines: string[]; frameIdx: number } {
  let bunnyFrames: readonly string[];
  let frameIdx: number;

  if (state.isJumping) {
    bunnyFrames = state.facingRight ? frames.jumpRight : frames.jumpLeft;
    frameIdx = state.jumpFrameIdx;
  } else if (state.currentAnimation === "idle") {
    bunnyFrames = state.facingRight ? frames.idleRight : frames.idleLeft;
    frameIdx = state.bunnyFrameIdx % bunnyFrames.length;
  } else if (state.currentAnimation === "walk_to_idle" || state.currentAnimation === "idle_to_walk") {
    bunnyFrames = state.facingRight ? frames.walkToIdleRight : frames.walkToIdleLeft;
    frameIdx = Math.max(0, Math.min(state.bunnyFrameIdx, bunnyFrames.length - 1));
  } else {
    bunnyFrames = state.facingRight ? frames.walkRight : frames.walkLeft;
    frameIdx = state.bunnyFrameIdx;
  }

  const frame = bunnyFrames[frameIdx];
  const lines = frame !== undefined ? frame.split("\n") : [];
  return { lines, frameIdx };
}
