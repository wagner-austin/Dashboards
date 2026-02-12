/**
 * @vitest-environment jsdom
 * Tests for keyboard input handling with unified input model.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { setupKeyboardControls, processDepthMovement, processHorizontalMovement, _test_hooks, type InputState } from "./Keyboard.js";
import { createBunnyTimers, type BunnyFrames, type BunnyState, type BunnyTimers, type AnimationState } from "../entities/Bunny.js";
import { calculateDepthBounds, createProjectionConfig, type DepthBounds } from "../world/Projection.js";
import { layerToWorldZ } from "../layers/widths.js";

const { CAMERA_Z_SPEED, CAMERA_X_SPEED, handleHopRelease, handleWalkKeyUp, isPendingJump, processInputChange } = _test_hooks;

/** Create test depth bounds matching default config (layers 8-30). */
function createTestDepthBounds(): DepthBounds {
  const projectionConfig = createProjectionConfig();
  const minTreeWorldZ = layerToWorldZ(8);
  const maxTreeWorldZ = layerToWorldZ(30);
  return calculateDepthBounds(minTreeWorldZ, maxTreeWorldZ, projectionConfig);
}

/** Standard test depth bounds. */
const TEST_DEPTH_BOUNDS = createTestDepthBounds();

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

function createTestInputState(bunnyState: BunnyState): InputState {
  return {
    bunny: bunnyState,
    viewport: { width: 100, height: 50, charW: 10, charH: 20 },
    camera: { x: 0, z: 0 },
    depthBounds: TEST_DEPTH_BOUNDS,
    horizontalHeld: null,
    verticalHeld: null,
  };
}

function dispatchKeyDown(key: string, repeat = false): void {
  document.dispatchEvent(new KeyboardEvent("keydown", { key, repeat }));
}

function dispatchKeyUp(key: string): void {
  document.dispatchEvent(new KeyboardEvent("keyup", { key }));
}

/**
 * Get animation state from bunny state.
 */
function getBunnyAnim(s: BunnyState): AnimationState {
  return s.animation;
}

describe("setupKeyboardControls", () => {
  let bunnyState: BunnyState;
  let state: InputState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    vi.useFakeTimers();
    bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    state = createTestInputState(bunnyState);
    frames = createTestFrames();
    timers = createBunnyTimers(bunnyState, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
      hop: 100,
    }, () => false);
    setupKeyboardControls(state, frames, timers);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("horizontal input (A/D keys)", () => {
    it("sets horizontalHeld to left when ArrowLeft pressed", () => {
      dispatchKeyDown("ArrowLeft");
      expect(state.horizontalHeld).toBe("left");
    });

    it("sets horizontalHeld to right when ArrowRight pressed", () => {
      dispatchKeyDown("ArrowRight");
      expect(state.horizontalHeld).toBe("right");
    });

    it("responds to a key (lowercase)", () => {
      dispatchKeyDown("a");
      expect(state.horizontalHeld).toBe("left");
    });

    it("responds to d key (lowercase)", () => {
      dispatchKeyDown("d");
      expect(state.horizontalHeld).toBe("right");
    });

    it("responds to A key (uppercase)", () => {
      dispatchKeyDown("A");
      expect(state.horizontalHeld).toBe("left");
    });

    it("responds to D key (uppercase)", () => {
      dispatchKeyDown("D");
      expect(state.horizontalHeld).toBe("right");
    });

    it("starts walk transition when pressing left from idle", () => {
      dispatchKeyDown("ArrowLeft");
      expect(state.bunny.animation.kind).toBe("transition");
      expect(state.bunny.facingRight).toBe(false);
    });

    it("starts walk transition when pressing right from idle", () => {
      dispatchKeyDown("ArrowRight");
      expect(state.bunny.animation.kind).toBe("transition");
      expect(state.bunny.facingRight).toBe(true);
    });

    it("clears horizontalHeld on left key release", () => {
      dispatchKeyDown("ArrowLeft");
      expect(state.horizontalHeld).toBe("left");
      dispatchKeyUp("ArrowLeft");
      expect(state.horizontalHeld).toBe(null);
    });

    it("clears horizontalHeld on right key release", () => {
      dispatchKeyDown("ArrowRight");
      expect(state.horizontalHeld).toBe("right");
      dispatchKeyUp("ArrowRight");
      expect(state.horizontalHeld).toBe(null);
    });

    it("only clears matching direction on release", () => {
      dispatchKeyDown("ArrowLeft");
      dispatchKeyUp("ArrowRight");
      expect(state.horizontalHeld).toBe("left");
    });

    it("ignores repeated key events", () => {
      dispatchKeyDown("ArrowLeft", true);
      expect(state.horizontalHeld).toBe(null);
    });
  });

  describe("vertical input (W/S keys)", () => {
    it("sets verticalHeld to up when W pressed", () => {
      dispatchKeyDown("w");
      expect(state.verticalHeld).toBe("up");
    });

    it("sets verticalHeld to down when S pressed", () => {
      dispatchKeyDown("s");
      expect(state.verticalHeld).toBe("down");
    });

    it("responds to ArrowUp", () => {
      dispatchKeyDown("ArrowUp");
      expect(state.verticalHeld).toBe("up");
    });

    it("responds to ArrowDown", () => {
      dispatchKeyDown("ArrowDown");
      expect(state.verticalHeld).toBe("down");
    });

    it("starts hop transition when pressing W from idle", () => {
      dispatchKeyDown("w");
      expect(state.bunny.animation.kind).toBe("transition");
    });

    it("clears verticalHeld on up key release", () => {
      dispatchKeyDown("w");
      expect(state.verticalHeld).toBe("up");
      dispatchKeyUp("w");
      expect(state.verticalHeld).toBe(null);
    });

    it("clears verticalHeld on down key release", () => {
      dispatchKeyDown("s");
      expect(state.verticalHeld).toBe("down");
      dispatchKeyUp("s");
      expect(state.verticalHeld).toBe(null);
    });

    it("only clears matching direction on release", () => {
      dispatchKeyDown("w");
      dispatchKeyUp("s");
      expect(state.verticalHeld).toBe("up");
    });
  });

  describe("diagonal input (D+W simultaneous)", () => {
    it("pressing D then W sets both horizontalHeld and verticalHeld", () => {
      dispatchKeyDown("d");
      expect(state.horizontalHeld).toBe("right");
      expect(state.verticalHeld).toBe(null);

      dispatchKeyDown("w");
      expect(state.horizontalHeld).toBe("right");
      expect(state.verticalHeld).toBe("up");
    });

    it("pressing W then D sets both inputs", () => {
      dispatchKeyDown("w");
      dispatchKeyDown("d");
      expect(state.horizontalHeld).toBe("right");
      expect(state.verticalHeld).toBe("up");
    });

    it("releasing W while holding D keeps horizontalHeld", () => {
      dispatchKeyDown("d");
      dispatchKeyDown("w");
      dispatchKeyUp("w");
      expect(state.horizontalHeld).toBe("right");
      expect(state.verticalHeld).toBe(null);
    });
  });

  describe("jump input (spacebar)", () => {
    it("starts jump transition when space pressed from idle", () => {
      dispatchKeyDown(" ");
      expect(state.bunny.animation.kind).toBe("transition");
    });

    it("ignores space during jump", () => {
      state.bunny.animation = { kind: "jump", frameIdx: 0 };
      dispatchKeyDown(" ");
      expect(state.bunny.animation.kind).toBe("jump");
    });
  });

  describe("reset (R key)", () => {
    it("resets camera position on R key", () => {
      state.camera = { x: 100, z: 50 };
      dispatchKeyDown("r");
      expect(state.camera.x).toBe(0);
    });
  });
});

describe("processInputChange", () => {
  let bunnyState: BunnyState;
  let state: InputState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    vi.useFakeTimers();
    bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    state = createTestInputState(bunnyState);
    frames = createTestFrames();
    timers = createBunnyTimers(bunnyState, frames, {
      walk: 100,
      idle: 200,
      jump: 50,
      transition: 80,
      hop: 100,
    }, () => false);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("starts hop when vertical input begins", () => {
    processInputChange(null, null, null, "up", state, frames, timers);
    expect(state.bunny.animation.kind).toBe("transition");
  });

  it("stops hop when vertical input ends", () => {
    state.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0 };
    timers.hop.start();

    processInputChange(null, "up", null, null, state, frames, timers);
    expect(state.bunny.animation.kind).toBe("idle");
  });

  it("switches hop direction from up to down", () => {
    state.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0 };
    timers.hop.start();

    processInputChange(null, "up", null, "down", state, frames, timers);
    expect(state.bunny.animation.kind).toBe("transition");
  });

  it("switches hop direction from down to up", () => {
    state.bunny.animation = { kind: "hop", direction: "toward", frameIdx: 0 };
    timers.hop.start();

    processInputChange(null, "down", null, "up", state, frames, timers);
    expect(state.bunny.animation.kind).toBe("transition");
  });

  it("starts walk when horizontal input begins and not hopping", () => {
    processInputChange(null, null, "left", null, state, frames, timers);
    expect(state.bunny.animation.kind).toBe("transition");
    expect(state.bunny.facingRight).toBe(false);
  });

  it("switches walk direction from left to right", () => {
    state.bunny.animation = { kind: "walk", frameIdx: 0 };

    processInputChange("left", null, "right", null, state, frames, timers);
    expect(state.bunny.facingRight).toBe(true);
  });

  it("stops walk when horizontal input ends", () => {
    state.bunny.animation = { kind: "walk", frameIdx: 0 };
    timers.walk.start();

    processInputChange("left", null, null, null, state, frames, timers);
    expect(state.bunny.animation.kind).toBe("transition");
  });

  it("does not start walk when hopping", () => {
    state.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0 };

    processInputChange(null, "up", "left", "up", state, frames, timers);
    // Animation should still be hop, not walk
    expect(state.bunny.animation.kind).toBe("hop");
  });

  it("does not start walk when vertical is held", () => {
    processInputChange(null, null, "left", "up", state, frames, timers);
    // Should start hop, not walk
    expect(state.bunny.animation.kind).toBe("transition");
  });

  it("updates facingRight when horizontal pressed during jump", () => {
    state.bunny.animation = { kind: "jump", frameIdx: 0 };
    state.bunny.facingRight = true;

    processInputChange(null, null, "left", null, state, frames, timers);

    expect(state.bunny.facingRight).toBe(false);
  });

  it("updates facingRight to right when horizontal right pressed during jump", () => {
    state.bunny.animation = { kind: "jump", frameIdx: 0 };
    state.bunny.facingRight = false;

    processInputChange(null, null, "right", null, state, frames, timers);

    expect(state.bunny.facingRight).toBe(true);
  });
});

describe("processDepthMovement", () => {
  function createTestState(animation: AnimationState): InputState {
    return createTestInputState(createTestBunnyState(animation));
  }

  /** Use 1 second delta for simple math: movement = speed * 1 */
  const DELTA_TIME = 1.0;

  it("does nothing when not hopping", () => {
    const state = createTestState({ kind: "idle", frameIdx: 0 });
    const initialZ = state.camera.z;

    processDepthMovement(state, DELTA_TIME);

    expect(state.camera.z).toBe(initialZ);
  });

  it("moves camera away (positive Z) when hopping away", () => {
    const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0 });
    const initialZ = state.camera.z;

    processDepthMovement(state, DELTA_TIME);

    expect(state.camera.z).toBe(initialZ + CAMERA_Z_SPEED);
  });

  it("moves camera toward (negative Z) when hopping toward", () => {
    const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 0 });
    const initialZ = state.camera.z;

    processDepthMovement(state, DELTA_TIME);

    expect(state.camera.z).toBe(initialZ - CAMERA_Z_SPEED);
  });

  it("wraps Z at max bound when moving away", () => {
    const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0 });
    state.camera = { x: 0, z: state.depthBounds.maxZ - 0.1 };

    processDepthMovement(state, DELTA_TIME);

    expect(state.camera.z).toBeLessThan(state.depthBounds.maxZ);
    expect(state.camera.z).toBeGreaterThanOrEqual(state.depthBounds.minZ);
  });

  it("wraps Z at min bound when moving toward", () => {
    const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 0 });
    state.camera = { x: 0, z: state.depthBounds.minZ + 0.1 };

    processDepthMovement(state, DELTA_TIME);

    expect(state.camera.z).toBeLessThan(state.depthBounds.maxZ);
  });
});

describe("processHorizontalMovement", () => {
  function createTestState(animation: AnimationState): InputState {
    return createTestInputState(createTestBunnyState(animation));
  }

  /** Use 1 second delta for simple math: movement = speed * 1 */
  const DELTA_TIME = 1.0;

  it("does nothing when not moving", () => {
    const state = createTestState({ kind: "idle", frameIdx: 0 });
    state.horizontalHeld = "left";
    const initialX = state.camera.x;

    processHorizontalMovement(state, DELTA_TIME);

    expect(state.camera.x).toBe(initialX);
  });

  it("does nothing when moving but no horizontal input", () => {
    const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0 });
    const initialX = state.camera.x;

    processHorizontalMovement(state, DELTA_TIME);

    expect(state.camera.x).toBe(initialX);
  });

  it("moves camera left when hopping with left held", () => {
    const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0 });
    state.horizontalHeld = "left";
    const initialX = state.camera.x;

    processHorizontalMovement(state, DELTA_TIME);

    expect(state.camera.x).toBe(initialX - CAMERA_X_SPEED);
  });

  it("moves camera right when hopping with right held", () => {
    const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0 });
    state.horizontalHeld = "right";
    const initialX = state.camera.x;

    processHorizontalMovement(state, DELTA_TIME);

    expect(state.camera.x).toBe(initialX + CAMERA_X_SPEED);
  });

  it("moves camera left when walking with left held", () => {
    const state = createTestState({ kind: "walk", frameIdx: 0 });
    state.horizontalHeld = "left";
    const initialX = state.camera.x;

    processHorizontalMovement(state, DELTA_TIME);

    expect(state.camera.x).toBe(initialX - CAMERA_X_SPEED);
  });

  it("moves camera right when walking with right held", () => {
    const state = createTestState({ kind: "walk", frameIdx: 0 });
    state.horizontalHeld = "right";
    const initialX = state.camera.x;

    processHorizontalMovement(state, DELTA_TIME);

    expect(state.camera.x).toBe(initialX + CAMERA_X_SPEED);
  });

  it("preserves camera.z when moving horizontally", () => {
    const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0 });
    state.horizontalHeld = "left";
    state.camera = { x: 0, z: 100 };

    processHorizontalMovement(state, DELTA_TIME);

    expect(state.camera.z).toBe(100);
  });

  it("does nothing during transition", () => {
    const state = createTestState({ kind: "transition", type: "idle_to_walk", frameIdx: 0, pendingAction: "walk", returnTo: "idle" });
    state.horizontalHeld = "left";
    const initialX = state.camera.x;

    processHorizontalMovement(state, DELTA_TIME);

    expect(state.camera.x).toBe(initialX);
  });

  it("moves camera during jump", () => {
    const state = createTestState({ kind: "jump", frameIdx: 0 });
    state.horizontalHeld = "left";
    const initialX = state.camera.x;

    processHorizontalMovement(state, DELTA_TIME);

    expect(state.camera.x).toBeLessThan(initialX);
  });
});

describe("isPendingJump", () => {
  it("returns false for idle", () => {
    const bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    expect(isPendingJump(bunny)).toBe(false);
  });

  it("returns false for walk", () => {
    const bunny = createTestBunnyState({ kind: "walk", frameIdx: 0 });
    expect(isPendingJump(bunny)).toBe(false);
  });

  it("returns false for jump", () => {
    const bunny = createTestBunnyState({ kind: "jump", frameIdx: 0 });
    expect(isPendingJump(bunny)).toBe(false);
  });

  it("returns false for transition without pending jump", () => {
    const bunny = createTestBunnyState({
      kind: "transition",
      type: "idle_to_walk",
      frameIdx: 0,
      pendingAction: "walk",
      returnTo: "idle",
    });
    expect(isPendingJump(bunny)).toBe(false);
  });

  it("returns true for transition with pending jump", () => {
    const bunny = createTestBunnyState({
      kind: "transition",
      type: "idle_to_walk",
      frameIdx: 0,
      pendingAction: "jump",
      returnTo: "idle",
    });
    expect(isPendingJump(bunny)).toBe(true);
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
    }, () => false);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("transitions from hop to idle when no horizontal held", () => {
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0 };
    timers.hop.start();

    handleHopRelease(bunnyState, timers, () => false);

    expect(bunnyState.animation.kind).toBe("idle");
    expect(timers.hop.isRunning()).toBe(false);
    expect(timers.idle.isRunning()).toBe(true);
  });

  it("transitions from hop to walk when horizontal held", () => {
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0 };
    timers.hop.start();

    handleHopRelease(bunnyState, timers, () => true);

    expect(bunnyState.animation.kind).toBe("walk");
    expect(timers.hop.isRunning()).toBe(false);
    expect(timers.walk.isRunning()).toBe(true);
  });

  it("cancels turn_away transition and returns to idle when no horizontal held", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_turn_away", frameIdx: 0, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleHopRelease(bunnyState, timers, () => false);

    expect(bunnyState.animation.kind).toBe("idle");
  });

  it("cancels turn_toward transition and returns to walk when horizontal held", () => {
    bunnyState.animation = { kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: "idle" };
    timers.transition.start();

    handleHopRelease(bunnyState, timers, () => true);

    expect(bunnyState.animation.kind).toBe("walk");
  });

  it("does nothing for non-hop animation", () => {
    bunnyState.animation = { kind: "walk", frameIdx: 0 };

    handleHopRelease(bunnyState, timers, () => false);

    expect(bunnyState.animation.kind).toBe("walk");
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
    }, () => false);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("transitions from walk to walk_to_idle", () => {
    bunnyState.animation = { kind: "walk", frameIdx: 1 };
    timers.walk.start();

    handleWalkKeyUp(bunnyState, timers);

    const anim = getBunnyAnim(bunnyState);
    expect(anim.kind).toBe("transition");
    if (anim.kind === "transition") {
      expect(anim.type).toBe("walk_to_idle");
    }
  });

  it("cancels idle_to_walk transition and returns to idle", () => {
    bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: "walk", returnTo: "idle" };
    timers.transition.start();

    handleWalkKeyUp(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("idle");
  });

  it("does nothing for hop animation", () => {
    bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0 };

    handleWalkKeyUp(bunnyState, timers);

    expect(bunnyState.animation.kind).toBe("hop");
  });
});
