/**
 * Tests for Bunny entity.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  createInitialBunnyState,
  createBunnyTimers,
  getBunnyFrame,
  type BunnyFrames,
  type BunnyState,
} from "./Bunny.js";

function createMockFrames(): BunnyFrames {
  return {
    walkLeft: ["walkL0", "walkL1", "walkL2"],
    walkRight: ["walkR0", "walkR1", "walkR2"],
    jumpLeft: ["jumpL0", "jumpL1", "jumpL2"],
    jumpRight: ["jumpR0", "jumpR1", "jumpR2"],
    idleLeft: ["idleL0", "idleL1"],
    idleRight: ["idleR0", "idleR1"],
    walkToIdleLeft: ["transL0", "transL1", "transL2"],
    walkToIdleRight: ["transR0", "transR1", "transR2"],
  };
}

function createTestBunnyState(overrides: Partial<BunnyState> = {}): BunnyState {
  return {
    facingRight: false,
    currentAnimation: "idle",
    bunnyFrameIdx: 0,
    isJumping: false,
    jumpFrameIdx: 0,
    isWalking: false,
    pendingJump: false,
    preJumpAnimation: null,
    ...overrides,
  };
}

describe("createInitialBunnyState", () => {
  it("returns default state facing left", () => {
    const state = createInitialBunnyState();
    expect(state.facingRight).toBe(false);
    expect(state.currentAnimation).toBe("idle");
    expect(state.bunnyFrameIdx).toBe(0);
    expect(state.isJumping).toBe(false);
    expect(state.jumpFrameIdx).toBe(0);
    expect(state.isWalking).toBe(false);
    expect(state.pendingJump).toBe(false);
    expect(state.preJumpAnimation).toBe(null);
  });
});

describe("createBunnyTimers", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("creates four timers", () => {
    const state = createInitialBunnyState();
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    expect(timers.walk).toBeDefined();
    expect(timers.idle).toBeDefined();
    expect(timers.jump).toBeDefined();
    expect(timers.transition).toBeDefined();
  });

  it("walk timer advances walk frame index", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "walk";
    state.isWalking = true;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.walk.start();
    expect(state.bunnyFrameIdx).toBe(0);

    vi.advanceTimersByTime(100);
    expect(state.bunnyFrameIdx).toBe(1);

    vi.advanceTimersByTime(100);
    expect(state.bunnyFrameIdx).toBe(2);

    vi.advanceTimersByTime(100);
    expect(state.bunnyFrameIdx).toBe(0); // Wraps
  });

  it("walk timer uses right frames when facing right", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "walk";
    state.facingRight = true;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.walk.start();
    vi.advanceTimersByTime(300);
    expect(state.bunnyFrameIdx).toBe(0); // 3 frames wrap to 0
  });

  it("idle timer advances idle frame index", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "idle";
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.idle.start();
    vi.advanceTimersByTime(200);
    expect(state.bunnyFrameIdx).toBe(1);

    vi.advanceTimersByTime(200);
    expect(state.bunnyFrameIdx).toBe(0); // 2 frames wrap
  });

  it("idle timer uses right frames when facing right", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "idle";
    state.facingRight = true;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.idle.start();
    vi.advanceTimersByTime(200);
    expect(state.bunnyFrameIdx).toBe(1); // idleRight has 2 frames
  });

  it("jump timer advances jump frame and ends jump", () => {
    const state = createInitialBunnyState();
    state.isJumping = true;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.jump.start();
    expect(state.jumpFrameIdx).toBe(0);

    vi.advanceTimersByTime(50);
    expect(state.jumpFrameIdx).toBe(1);

    vi.advanceTimersByTime(50);
    expect(state.jumpFrameIdx).toBe(2);

    vi.advanceTimersByTime(50);
    expect(state.isJumping).toBe(false);
    expect(state.jumpFrameIdx).toBe(0);
  });

  it("jump timer uses right frames when facing right", () => {
    const state = createInitialBunnyState();
    state.isJumping = true;
    state.facingRight = true;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.jump.start();
    vi.advanceTimersByTime(150); // Complete full jump (3 frames)
    expect(state.isJumping).toBe(false);
    expect(state.jumpFrameIdx).toBe(0);
  });

  it("jump timer starts walk_to_idle transition when preJumpAnimation is idle", () => {
    const state = createInitialBunnyState();
    state.isJumping = true;
    state.preJumpAnimation = "idle";
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.jump.start();
    vi.advanceTimersByTime(150); // Complete jump (3 frames)

    // Should transition back to idle via walk_to_idle
    expect(state.isJumping).toBe(false);
    expect(state.currentAnimation).toBe("walk_to_idle");
    expect(state.bunnyFrameIdx).toBe(0);
    expect(state.preJumpAnimation).toBe(null);
    expect(timers.transition.isRunning()).toBe(true);
  });

  it("jump timer resumes walk when preJumpAnimation is walk", () => {
    const state = createInitialBunnyState();
    state.isJumping = true;
    state.preJumpAnimation = "walk";
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.jump.start();
    vi.advanceTimersByTime(150); // Complete jump (3 frames)

    // Should resume walking
    expect(state.isJumping).toBe(false);
    expect(state.currentAnimation).toBe("walk");
    expect(state.bunnyFrameIdx).toBe(0);
    expect(state.preJumpAnimation).toBe(null);
    expect(timers.walk.isRunning()).toBe(true);
  });

  it("transition timer starts jump when pendingJump is true after idle_to_walk", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "idle_to_walk";
    state.bunnyFrameIdx = 2; // Last frame of transition (3 frames)
    state.pendingJump = true;
    state.preJumpAnimation = "idle";
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.transition.start();
    vi.advanceTimersByTime(80); // bunnyFrameIdx becomes 1
    vi.advanceTimersByTime(80); // bunnyFrameIdx becomes 0
    vi.advanceTimersByTime(80); // bunnyFrameIdx becomes -1, triggers jump

    expect(state.pendingJump).toBe(false);
    expect(state.isJumping).toBe(true);
    expect(state.jumpFrameIdx).toBe(0);
    expect(timers.jump.isRunning()).toBe(true);
  });

  it("transition timer advances walk_to_idle and switches to idle", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "walk_to_idle";
    state.bunnyFrameIdx = 0;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.transition.start();
    vi.advanceTimersByTime(80);
    expect(state.bunnyFrameIdx).toBe(1);

    vi.advanceTimersByTime(80);
    expect(state.bunnyFrameIdx).toBe(2);

    vi.advanceTimersByTime(80);
    expect(state.currentAnimation).toBe("idle");
    expect(state.bunnyFrameIdx).toBe(0);
  });

  it("transition timer uses right frames when facing right during walk_to_idle", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "walk_to_idle";
    state.facingRight = true;
    state.bunnyFrameIdx = 0;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.transition.start();
    vi.advanceTimersByTime(240); // Complete full transition (3 frames)
    expect(state.currentAnimation).toBe("idle");
    expect(state.bunnyFrameIdx).toBe(0);
  });

  it("transition timer reverses idle_to_walk and switches to walk", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "idle_to_walk";
    state.bunnyFrameIdx = 2;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.transition.start();
    vi.advanceTimersByTime(80);
    expect(state.bunnyFrameIdx).toBe(1);

    vi.advanceTimersByTime(80);
    expect(state.bunnyFrameIdx).toBe(0);

    vi.advanceTimersByTime(80);
    expect(state.currentAnimation).toBe("walk");
    expect(state.bunnyFrameIdx).toBe(0);
  });

  it("transition timer uses right frames when facing right during idle_to_walk", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "idle_to_walk";
    state.facingRight = true;
    state.bunnyFrameIdx = 2;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.transition.start();
    vi.advanceTimersByTime(240); // Complete full transition
    expect(state.currentAnimation).toBe("walk");
    expect(state.bunnyFrameIdx).toBe(0);
  });

  it("walk timer does not advance during jump", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "walk";
    state.isJumping = true;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.walk.start();
    vi.advanceTimersByTime(100);
    expect(state.bunnyFrameIdx).toBe(0); // No change
  });

  it("idle timer does not advance when not in idle animation", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "walk"; // Not idle
    state.isJumping = false;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.idle.start();
    vi.advanceTimersByTime(200);
    expect(state.bunnyFrameIdx).toBe(0); // No change
  });

  it("idle timer does not advance during jump", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "idle";
    state.isJumping = true;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.idle.start();
    vi.advanceTimersByTime(200);
    expect(state.bunnyFrameIdx).toBe(0); // No change
  });

  it("transition timer does not advance during jump", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "walk_to_idle";
    state.isJumping = true;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.transition.start();
    vi.advanceTimersByTime(80);
    expect(state.bunnyFrameIdx).toBe(0); // No change
  });

  it("transition timer does nothing when animation is neither walk_to_idle nor idle_to_walk", () => {
    const state = createInitialBunnyState();
    state.currentAnimation = "walk"; // Not a transition animation
    state.bunnyFrameIdx = 1;
    const frames = createMockFrames();
    const timers = createBunnyTimers(state, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
    });

    timers.transition.start();
    vi.advanceTimersByTime(80);
    expect(state.bunnyFrameIdx).toBe(1); // No change
    expect(state.currentAnimation).toBe("walk"); // Still walk
  });
});

describe("getBunnyFrame", () => {
  it("returns jump frame when jumping facing left", () => {
    const state = createTestBunnyState({
      currentAnimation: "walk",
      bunnyFrameIdx: 1,
      isJumping: true,
      jumpFrameIdx: 2,
      isWalking: true,
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual(["jumpL2"]);
    expect(result.frameIdx).toBe(2);
  });

  it("returns jump frame when jumping facing right", () => {
    const state = createTestBunnyState({
      facingRight: true,
      currentAnimation: "walk",
      bunnyFrameIdx: 1,
      isJumping: true,
      jumpFrameIdx: 1,
      isWalking: true,
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual(["jumpR1"]);
    expect(result.frameIdx).toBe(1);
  });

  it("returns idle frame when in idle animation facing right", () => {
    const state = createTestBunnyState({
      facingRight: true,
      bunnyFrameIdx: 1,
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual(["idleR1"]);
  });

  it("returns idle frame when in idle animation facing left", () => {
    const state = createTestBunnyState();
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual(["idleL0"]);
  });

  it("returns transition frame for walk_to_idle facing left", () => {
    const state = createTestBunnyState({
      currentAnimation: "walk_to_idle",
      bunnyFrameIdx: 1,
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual(["transL1"]);
  });

  it("returns transition frame for walk_to_idle facing right", () => {
    const state = createTestBunnyState({
      facingRight: true,
      currentAnimation: "walk_to_idle",
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual(["transR0"]);
  });

  it("returns transition frame for idle_to_walk", () => {
    const state = createTestBunnyState({
      facingRight: true,
      currentAnimation: "idle_to_walk",
      bunnyFrameIdx: 2,
      isWalking: true,
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual(["transR2"]);
  });

  it("returns walk frame when walking right", () => {
    const state = createTestBunnyState({
      facingRight: true,
      currentAnimation: "walk",
      isWalking: true,
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual(["walkR0"]);
  });

  it("returns walk frame when walking left", () => {
    const state = createTestBunnyState({
      currentAnimation: "walk",
      bunnyFrameIdx: 1,
      isWalking: true,
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual(["walkL1"]);
    expect(result.frameIdx).toBe(1);
  });

  it("clamps transition frame index to valid range", () => {
    const state = createTestBunnyState({
      currentAnimation: "walk_to_idle",
      bunnyFrameIdx: 100, // Out of range
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.frameIdx).toBe(2); // Clamped to max
  });

  it("handles negative transition frame index", () => {
    const state = createTestBunnyState({
      currentAnimation: "idle_to_walk",
      bunnyFrameIdx: -5,
      isWalking: true,
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.frameIdx).toBe(0); // Clamped to min
  });

  it("wraps idle frame index", () => {
    const state = createTestBunnyState({
      bunnyFrameIdx: 5, // Greater than frame count
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.frameIdx).toBe(1); // 5 % 2 = 1
  });

  it("returns empty lines when frame index is out of bounds", () => {
    const state = createTestBunnyState({
      currentAnimation: "walk",
      bunnyFrameIdx: 999, // Way out of bounds
      isWalking: true,
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual([]);
    expect(result.frameIdx).toBe(999);
  });

  it("returns empty lines when jump frame index is out of bounds", () => {
    const state = createTestBunnyState({
      facingRight: true,
      currentAnimation: "walk",
      isJumping: true,
      jumpFrameIdx: 999, // Way out of bounds
    });
    const frames = createMockFrames();

    const result = getBunnyFrame(state, frames);
    expect(result.lines).toEqual([]);
    expect(result.frameIdx).toBe(999);
  });
});
