/**
 * @vitest-environment jsdom
 * Tests for the walk and jump input handlers.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { _test_hooks } from "./handlers.js";
import type { AnimationState, BunnyFrames, BunnyState, BunnyTimers } from "../entities/Bunny.js";
import {
  createTestBunnyState,
  createTestFrames,
  createTestTimers,
} from "../testing/fixtures.js";

const { isPendingJump, handleJumpInput, handleWalkKeyDown, handleWalkKeyUp } = _test_hooks;

/**
 * Read the animation out of a bunny state.
 *
 * Args:
 *     s: Bunny state to read.
 *
 * Returns:
 *     The current animation state.
 */
function getBunnyAnim(s: BunnyState): AnimationState {
  return s.animation;
}

describe("isPendingJump", () => {
  it("returns true when transition has pending jump action", () => {
    const bunny = createTestBunnyState({ kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "jump", returnTo: "idle" });
    expect(isPendingJump(bunny)).toBe(true);
  });

  it("returns false when transition has different pending action", () => {
    const bunny = createTestBunnyState({ kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "walk", returnTo: "idle" });
    expect(isPendingJump(bunny)).toBe(false);
  });

  it("returns false when not in transition", () => {
    const bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    expect(isPendingJump(bunny)).toBe(false);
  });

  it("returns false when transition has null pending action", () => {
    const bunny = createTestBunnyState({ kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" });
    expect(isPendingJump(bunny)).toBe(false);
  });

  it("returns false for walk state", () => {
    const bunny = createTestBunnyState({ kind: "walk", frameIdx: 0 });
    expect(isPendingJump(bunny)).toBe(false);
  });

  it("returns false for hop state", () => {
    const bunny = createTestBunnyState({ kind: "hop", direction: "away", frameIdx: 0 });
    expect(isPendingJump(bunny)).toBe(false);
  });

  it("returns false for jump state", () => {
    const bunny = createTestBunnyState({ kind: "jump", frameIdx: 0 });
    expect(isPendingJump(bunny)).toBe(false);
  });
});

describe("handleJumpInput", () => {
  let bunnyState: BunnyState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    vi.useFakeTimers();
    bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    frames = createTestFrames();
    timers = createTestTimers(bunnyState, frames, () => false);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("starts transition with pending jump when called from idle", () => {
    handleJumpInput(bunnyState, frames, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("idle_to_walk");
      expect(anim.pendingAction).toBe("jump");
      expect(anim.returnTo).toBe("idle");
    }
    expect(timers.idle.isRunning()).toBe(false);
    expect(timers.transition.isRunning()).toBe(true);
  });

  it("uses correct frame index based on walkToIdleLeft length", () => {
    bunnyState.facingRight = false;
    handleJumpInput(bunnyState, frames, timers);

    if (bunnyState.animation.kind === "transition") {
      expect(bunnyState.animation.frameIdx).toBe(2); // walkToIdleLeft.length - 1
    }
  });

  it("uses correct frame index based on walkToIdleRight length", () => {
    bunnyState.facingRight = true;
    handleJumpInput(bunnyState, frames, timers);

    if (bunnyState.animation.kind === "transition") {
      expect(bunnyState.animation.frameIdx).toBe(2); // walkToIdleRight.length - 1
    }
  });

  it("starts jump immediately when called from walk", () => {
    bunnyState.animation = { kind: "walk", frameIdx: 0 };
    timers.walk.start();

    handleJumpInput(bunnyState, frames, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("jump");
    if (anim.kind === "jump") {
      expect(anim.frameIdx).toBe(0);
    }
    expect(timers.walk.isRunning()).toBe(false);
    expect(timers.jump.isRunning()).toBe(true);
  });

  it("starts jump immediately when called from transition", () => {
    bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleJumpInput(bunnyState, frames, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("jump");
    expect(timers.transition.isRunning()).toBe(false);
    expect(timers.jump.isRunning()).toBe(true);
  });

  it("starts jump from walk_to_idle transition", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleJumpInput(bunnyState, frames, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("jump");
  });

  it("does nothing when called from hop state", () => {
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0 };

    handleJumpInput(bunnyState, frames, timers);

    expect(bunnyState.animation.kind).toBe("hop");
  });

  it("does nothing when called from jump state", () => {
    bunnyState.animation = { kind: "jump", frameIdx: 0 };

    handleJumpInput(bunnyState, frames, timers);

    expect(bunnyState.animation.kind).toBe("jump");
  });
});

describe("handleWalkKeyDown", () => {
  let bunnyState: BunnyState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    vi.useFakeTimers();
    bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    frames = createTestFrames();
    timers = createTestTimers(bunnyState, frames, () => false);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("starts transition to walk when called from idle going right", () => {
    handleWalkKeyDown(bunnyState, frames, timers, true);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("idle_to_walk");
      expect(anim.pendingAction).toBe("walk");
    }
    expect(bunnyState.facingRight).toBe(true);
    expect(timers.idle.isRunning()).toBe(false);
    expect(timers.transition.isRunning()).toBe(true);
  });

  it("starts transition to walk when called from idle going left", () => {
    handleWalkKeyDown(bunnyState, frames, timers, false);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("idle_to_walk");
      expect(anim.pendingAction).toBe("walk");
    }
    expect(bunnyState.facingRight).toBe(false);
  });

  it("interrupts transition and starts walk immediately", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleWalkKeyDown(bunnyState, frames, timers, true);

    expect(bunnyState.animation.kind).toBe("walk");
    expect(bunnyState.facingRight).toBe(true);
    expect(timers.transition.isRunning()).toBe(false);
    expect(timers.walk.isRunning()).toBe(true);
  });

  it("switches direction when already walking", () => {
    bunnyState.animation = { kind: "walk", frameIdx: 3 };
    bunnyState.facingRight = false;

    handleWalkKeyDown(bunnyState, frames, timers, true);

    expect(bunnyState.animation.kind).toBe("walk");
    expect(bunnyState.facingRight).toBe(true);
    expect(bunnyState.animation.frameIdx).toBe(0);
  });

  it("resets frame when same direction while walking", () => {
    bunnyState.animation = { kind: "walk", frameIdx: 3 };
    bunnyState.facingRight = true;

    handleWalkKeyDown(bunnyState, frames, timers, true);

    expect(bunnyState.animation.kind).toBe("walk");
    expect(bunnyState.animation.frameIdx).toBe(0);
  });

  it("does nothing when called from hop state", () => {
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0 };

    handleWalkKeyDown(bunnyState, frames, timers, true);

    expect(bunnyState.animation.kind).toBe("hop");
  });

  it("does nothing when called from jump state", () => {
    bunnyState.animation = { kind: "jump", frameIdx: 0 };

    handleWalkKeyDown(bunnyState, frames, timers, true);

    expect(bunnyState.animation.kind).toBe("jump");
  });
});

describe("handleWalkKeyUp", () => {
  let bunnyState: BunnyState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    vi.useFakeTimers();
    bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    frames = createTestFrames();
    timers = createTestTimers(bunnyState, frames, () => false);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("transitions from walk to walk_to_idle when key released", () => {
    bunnyState.animation = { kind: "walk", frameIdx: 1 };
    timers.walk.start();

    handleWalkKeyUp(bunnyState, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("walk_to_idle");
      expect(anim.frameIdx).toBe(0);
      expect(anim.pendingAction).toBe(null);
      expect(anim.returnTo).toBe("idle");
    }
    expect(timers.walk.isRunning()).toBe(false);
    expect(timers.transition.isRunning()).toBe(true);
  });

  it("cancels idle_to_walk transition and returns to idle", () => {
    bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: "walk", returnTo: "idle" };
    timers.transition.start();

    handleWalkKeyUp(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("idle");
    expect(bunnyState.animation.frameIdx).toBe(0);
    expect(timers.transition.isRunning()).toBe(false);
    expect(timers.idle.isRunning()).toBe(true);
  });

  it("does nothing when in idle state", () => {
    bunnyState.animation = { kind: "idle", frameIdx: 0 };

    handleWalkKeyUp(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("idle");
  });

  it("does nothing when in hop state", () => {
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0 };

    handleWalkKeyUp(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("hop");
  });

  it("does nothing when in jump state", () => {
    bunnyState.animation = { kind: "jump", frameIdx: 0 };

    handleWalkKeyUp(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("jump");
  });

  it("does nothing when in walk_to_idle transition", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleWalkKeyUp(bunnyState, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("walk_to_idle");
    }
    expect(timers.transition.isRunning()).toBe(true);
  });

  it("does nothing when in walk_to_turn transition", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_turn_away", frameIdx: 0, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleWalkKeyUp(bunnyState, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("walk_to_turn_away");
    }
  });
});

