/**
 * @vitest-environment jsdom
 * Tests for shared input handlers.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { _test_hooks } from "./handlers.js";
import { createBunnyTimers, type BunnyFrames, type BunnyState, type BunnyTimers, type AnimationState } from "../entities/Bunny.js";

const {
  isPendingJump,
  handleJumpInput,
  handleWalkKeyDown,
  handleWalkKeyUp,
  handleHopInput,
  handleHopRelease,
} = _test_hooks;

function createTestFrames(): BunnyFrames {
  return {
    walkLeft: ["walkL0", "walkL1"],
    walkRight: ["walkR0", "walkR1"],
    jumpLeft: ["jumpL0"],
    jumpRight: ["jumpR0"],
    idleLeft: ["idleL0"],
    idleRight: ["idleR0"],
    walkToIdleLeft: ["transL0", "transL1", "transL2"],
    walkToIdleRight: ["transR0", "transR1", "transR2"],
    walkToTurnAwayLeft: ["turnAwayL0", "turnAwayL1"],
    walkToTurnAwayRight: ["turnAwayR0", "turnAwayR1"],
    walkToTurnTowardLeft: ["turnTowardL0", "turnTowardL1"],
    walkToTurnTowardRight: ["turnTowardR0", "turnTowardR1"],
    hopAway: ["hopAway0", "hopAway1"],
    hopToward: ["hopToward0", "hopToward1"],
  };
}

function createTestBunnyState(animation: AnimationState, facingRight = false): BunnyState {
  return { facingRight, animation };
}

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
    const bunny = createTestBunnyState({ kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" });
    expect(isPendingJump(bunny)).toBe(false);
  });

  it("returns false for jump state", () => {
    const bunny = createTestBunnyState({ kind: "jump", frameIdx: 0, returnTo: "idle" });
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
    timers = createBunnyTimers(bunnyState, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
      hop: 100,
    });
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
      expect(anim.returnTo).toBe("walk");
      expect(anim.frameIdx).toBe(0);
    }
    expect(timers.walk.isRunning()).toBe(false);
    expect(timers.jump.isRunning()).toBe(true);
  });

  it("starts jump immediately when called from transition with returnTo walk", () => {
    bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: null, returnTo: "walk" };
    timers.transition.start();

    handleJumpInput(bunnyState, frames, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("jump");
    if (anim.kind === "jump") {
      expect(anim.returnTo).toBe("walk");
    }
    expect(timers.transition.isRunning()).toBe(false);
    expect(timers.jump.isRunning()).toBe(true);
  });

  it("starts jump with returnTo idle when called from transition with returnTo idle", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleJumpInput(bunnyState, frames, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("jump");
    if (anim.kind === "jump") {
      expect(anim.returnTo).toBe("idle");
    }
  });

  it("does nothing when called from hop state", () => {
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };

    handleJumpInput(bunnyState, frames, timers);

    expect(bunnyState.animation.kind).toBe("hop");
  });

  it("does nothing when called from jump state", () => {
    bunnyState.animation = { kind: "jump", frameIdx: 0, returnTo: "idle" };

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
    timers = createBunnyTimers(bunnyState, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
      hop: 100,
    });
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
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };

    handleWalkKeyDown(bunnyState, frames, timers, true);

    expect(bunnyState.animation.kind).toBe("hop");
  });

  it("does nothing when called from jump state", () => {
    bunnyState.animation = { kind: "jump", frameIdx: 0, returnTo: "idle" };

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
    timers = createBunnyTimers(bunnyState, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
      hop: 100,
    });
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
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };

    handleWalkKeyUp(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("hop");
  });

  it("does nothing when in jump state", () => {
    bunnyState.animation = { kind: "jump", frameIdx: 0, returnTo: "idle" };

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

describe("handleHopInput", () => {
  let bunnyState: BunnyState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    vi.useFakeTimers();
    bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    frames = createTestFrames();
    timers = createBunnyTimers(bunnyState, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
      hop: 100,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("starts turn away transition when called from idle with away direction", () => {
    handleHopInput(bunnyState, timers, "away");

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("walk_to_turn_away");
      expect(anim.returnTo).toBe("idle");
      expect(anim.pendingAction).toBe(null);
    }
    expect(timers.idle.isRunning()).toBe(false);
    expect(timers.transition.isRunning()).toBe(true);
  });

  it("starts turn toward transition when called from idle with toward direction", () => {
    handleHopInput(bunnyState, timers, "toward");

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("walk_to_turn_toward");
      expect(anim.returnTo).toBe("idle");
    }
  });

  it("starts turn away transition when called from walk", () => {
    bunnyState.animation = { kind: "walk", frameIdx: 0 };
    timers.walk.start();

    handleHopInput(bunnyState, timers, "away");

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("walk_to_turn_away");
      expect(anim.returnTo).toBe("walk");
    }
    expect(timers.walk.isRunning()).toBe(false);
    expect(timers.transition.isRunning()).toBe(true);
  });

  it("starts turn toward transition when called from walk", () => {
    bunnyState.animation = { kind: "walk", frameIdx: 0 };
    timers.walk.start();

    handleHopInput(bunnyState, timers, "toward");

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("walk_to_turn_toward");
      expect(anim.returnTo).toBe("walk");
    }
  });

  it("sets pendingAction when called during transition", () => {
    bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: "walk", returnTo: "idle" };

    handleHopInput(bunnyState, timers, "away");

    const anim = getBunnyAnim(bunnyState);
    if (anim.kind === "transition") {
      expect(anim.pendingAction).toBe("hop_away");
    }
  });

  it("sets pendingAction to hop_toward when called with toward direction during transition", () => {
    bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: "walk", returnTo: "idle" };

    handleHopInput(bunnyState, timers, "toward");

    const anim = getBunnyAnim(bunnyState);
    if (anim.kind === "transition") {
      expect(anim.pendingAction).toBe("hop_toward");
    }
  });

  it("does nothing when already jumping", () => {
    bunnyState.animation = { kind: "jump", frameIdx: 0, returnTo: "idle" };

    handleHopInput(bunnyState, timers, "away");

    expect(bunnyState.animation.kind).toBe("jump");
  });

  it("does nothing when already hopping", () => {
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };

    handleHopInput(bunnyState, timers, "toward");

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("hop");
    if (anim.kind === "hop") {
      expect(anim.direction).toBe("away");
    }
  });
});

describe("handleHopRelease", () => {
  let bunnyState: BunnyState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    vi.useFakeTimers();
    bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    frames = createTestFrames();
    timers = createBunnyTimers(bunnyState, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
      hop: 100,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("clears hop pendingAction from idle_to_walk transition", () => {
    bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "hop_away", returnTo: "idle" };
    timers.transition.start();

    handleHopRelease(bunnyState, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("idle_to_walk");
      expect(anim.pendingAction).toBe(null);
    }
    expect(timers.transition.isRunning()).toBe(true);
  });

  it("clears hop_toward pendingAction from idle_to_walk same as hop_away", () => {
    bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: "hop_toward", returnTo: "idle" };
    timers.transition.start();

    handleHopRelease(bunnyState, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.pendingAction).toBe(null);
    }
  });

  it("cancels walk_to_turn_away transition and returns to walk when returnTo is walk", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_turn_away", frameIdx: 1, pendingAction: null, returnTo: "walk" };
    timers.transition.start();

    handleHopRelease(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("walk");
    expect(timers.walk.isRunning()).toBe(true);
    expect(timers.transition.isRunning()).toBe(false);
  });

  it("cancels walk_to_turn_away transition and returns to idle when returnTo is idle", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_turn_away", frameIdx: 1, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleHopRelease(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("idle");
    expect(timers.idle.isRunning()).toBe(true);
    expect(timers.transition.isRunning()).toBe(false);
  });

  it("cancels walk_to_turn_toward transition and returns to walk when returnTo is walk", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: "walk" };
    timers.transition.start();

    handleHopRelease(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("walk");
    expect(timers.walk.isRunning()).toBe(true);
  });

  it("cancels walk_to_turn_toward transition and returns to idle when returnTo is idle", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleHopRelease(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("idle");
    expect(timers.idle.isRunning()).toBe(true);
  });

  it("does nothing for walk_to_idle transition", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleHopRelease(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("transition");
    expect(timers.transition.isRunning()).toBe(true);
  });

  it("does nothing for non-transition, non-hop state", () => {
    bunnyState.animation = { kind: "walk", frameIdx: 0 };

    handleHopRelease(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("walk");
  });

  it("does nothing for idle state", () => {
    bunnyState.animation = { kind: "idle", frameIdx: 0 };

    handleHopRelease(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("idle");
  });

  it("stops hop and returns to walk when returnTo is walk", () => {
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 1, returnTo: "walk" };
    timers.hop.start();

    handleHopRelease(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("walk");
    expect(timers.walk.isRunning()).toBe(true);
    expect(timers.hop.isRunning()).toBe(false);
  });

  it("stops hop and returns to idle when returnTo is idle", () => {
    bunnyState.animation = { kind: "hop", direction: "toward", frameIdx: 0, returnTo: "idle" };
    timers.hop.start();

    handleHopRelease(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("idle");
    expect(timers.idle.isRunning()).toBe(true);
    expect(timers.hop.isRunning()).toBe(false);
  });

  it("does not cancel walk_to_idle transition even with pending hop", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: "hop_away", returnTo: "idle" };
    timers.transition.start();

    handleHopRelease(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("transition");
  });
});
