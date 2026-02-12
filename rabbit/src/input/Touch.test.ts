/**
 * @vitest-environment happy-dom
 * Tests for touch input handling.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  setupTouchControls,
  createTouchState,
  calculateDirection,
  isTap,
  processDirectionChange,
  handleTouchEnd,
  handleTouchStart,
  handleTouchMove,
  handleTouchEndEvent,
  DEFAULT_TOUCH_CONFIG,
  type JoystickState,
  type TouchState,
} from "./Touch.js";
import type { InputState } from "./Keyboard.js";
import { createBunnyTimers, type BunnyFrames, type BunnyState, type BunnyTimers, type AnimationState } from "../entities/Bunny.js";
import { calculateDepthBounds, createProjectionConfig, type DepthBounds } from "../world/Projection.js";
import { layerToWorldZ } from "../layers/widths.js";

function createTestDepthBounds(): DepthBounds {
  const projectionConfig = createProjectionConfig();
  return calculateDepthBounds(layerToWorldZ(8), layerToWorldZ(30), projectionConfig);
}

const TEST_DEPTH_BOUNDS = createTestDepthBounds();

function createTestFrames(): BunnyFrames {
  return {
    walkLeft: ["wL0", "wL1"],
    walkRight: ["wR0", "wR1"],
    jumpLeft: ["jL0"],
    jumpRight: ["jR0"],
    idleLeft: ["iL0"],
    idleRight: ["iR0"],
    walkToIdleLeft: ["t0", "t1", "t2"],
    walkToIdleRight: ["t0", "t1", "t2"],
    walkToTurnAwayLeft: ["ta0", "ta1"],
    walkToTurnAwayRight: ["ta0", "ta1"],
    walkToTurnTowardLeft: ["tt0", "tt1"],
    walkToTurnTowardRight: ["tt0", "tt1"],
    hopAway: ["ha0", "ha1"],
    hopToward: ["ht0", "ht1"],
  };
}

function createTestBunnyState(animation: AnimationState): BunnyState {
  return { facingRight: false, animation };
}

function createTestInputState(bunny: BunnyState): InputState {
  return {
    bunny,
    viewport: { width: 100, height: 50, charW: 10, charH: 20 },
    camera: { x: 0, z: 0 },
    depthBounds: TEST_DEPTH_BOUNDS,
    hopKeyHeld: null,
    slideKeyHeld: null,
    walkKeyHeld: null,
  };
}

function createJoystick(dx: number, dy: number, startTime = 0): JoystickState {
  return {
    anchorX: 100,
    anchorY: 100,
    currentX: 100 + dx,
    currentY: 100 + dy,
    startTime,
    identifier: 0,
  };
}

/**
 * Create mock TouchList for testing.
 */
function createMockTouchList(touches: readonly { identifier: number; clientX: number; clientY: number }[]): TouchList {
  const list = touches.map(t => t as Touch);
  return Object.assign(list, {
    item: (i: number): Touch | null => list[i] ?? null,
  }) as unknown as TouchList;
}

describe("createTouchState", () => {
  it("creates initial state with no joystick", () => {
    const state = createTouchState();
    expect(state.joystick).toBe(null);
    expect(state.currentDirection).toBe(null);
  });
});

describe("calculateDirection", () => {
  const config = DEFAULT_TOUCH_CONFIG;

  it("returns null within deadzone", () => {
    expect(calculateDirection(createJoystick(0, 0), config)).toBe(null);
    expect(calculateDirection(createJoystick(10, 10), config)).toBe(null);
  });

  it("returns correct 8-way directions", () => {
    // Cardinal directions
    expect(calculateDirection(createJoystick(50, 0), config)).toBe("right");
    expect(calculateDirection(createJoystick(-50, 0), config)).toBe("left");
    expect(calculateDirection(createJoystick(0, -50), config)).toBe("up");
    expect(calculateDirection(createJoystick(0, 50), config)).toBe("down");

    // Diagonal directions
    expect(calculateDirection(createJoystick(50, -50), config)).toBe("up-right");
    expect(calculateDirection(createJoystick(-50, -50), config)).toBe("up-left");
    expect(calculateDirection(createJoystick(50, 50), config)).toBe("down-right");
    expect(calculateDirection(createJoystick(-50, 50), config)).toBe("down-left");
  });

  it("handles boundary angles correctly", () => {
    // Small deviations should still map to nearest direction
    expect(calculateDirection(createJoystick(50, 10), config)).toBe("right");
    expect(calculateDirection(createJoystick(50, -10), config)).toBe("right");
    expect(calculateDirection(createJoystick(10, -50), config)).toBe("up");
    expect(calculateDirection(createJoystick(-10, -50), config)).toBe("up");
  });
});

describe("isTap", () => {
  const config = DEFAULT_TOUCH_CONFIG;

  it("returns true for quick touch with minimal movement", () => {
    expect(isTap(createJoystick(5, 5, 1000), 1100, config)).toBe(true);
    expect(isTap(createJoystick(0, 0, 1000), 1050, config)).toBe(true);
  });

  it("returns false for long touch or too much movement", () => {
    expect(isTap(createJoystick(5, 5, 1000), 1300, config)).toBe(false); // too long
    expect(isTap(createJoystick(50, 0, 1000), 1100, config)).toBe(false); // too far
  });
});

describe("processDirectionChange", () => {
  let inputState: InputState;
  let touchState: TouchState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    vi.useFakeTimers();
    inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
    touchState = createTouchState();
    frames = createTestFrames();
    timers = createBunnyTimers(inputState.bunny, frames, {
      walk: 100, idle: 200, jump: 50, transition: 80, hop: 100,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("starts hop when moving up/down", () => {
    processDirectionChange(null, "up", touchState, inputState, frames, timers);
    expect(inputState.hopKeyHeld).toBe("away");

    inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
    touchState = createTouchState();
    processDirectionChange(null, "down", touchState, inputState, frames, timers);
    expect(inputState.hopKeyHeld).toBe("toward");
  });

  it("starts walk when moving left/right", () => {
    processDirectionChange(null, "left", touchState, inputState, frames, timers);
    expect(inputState.walkKeyHeld).toBe("left");

    inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
    touchState = createTouchState();
    processDirectionChange(null, "right", touchState, inputState, frames, timers);
    expect(inputState.walkKeyHeld).toBe("right");
  });

  it("sets slide during hop for diagonal movement", () => {
    // Start hopping
    inputState.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };
    inputState.hopKeyHeld = "away";

    processDirectionChange("up", "up-left", touchState, inputState, frames, timers);
    expect(inputState.slideKeyHeld).toBe("left");

    processDirectionChange("up-left", "up-right", touchState, inputState, frames, timers);
    expect(inputState.slideKeyHeld).toBe("right");
  });

  it("ends hop when leaving vertical direction", () => {
    inputState.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };
    inputState.hopKeyHeld = "away";
    timers.hop.start();

    processDirectionChange("up", null, touchState, inputState, frames, timers);
    expect(inputState.hopKeyHeld).toBe(null);
  });

  it("switches hop direction between up and down", () => {
    inputState.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };
    inputState.hopKeyHeld = "away";
    timers.hop.start();

    processDirectionChange("up", "down", touchState, inputState, frames, timers);
    expect(inputState.hopKeyHeld).toBe("toward");
  });

  it("switches hop direction from down to up", () => {
    inputState.bunny.animation = { kind: "hop", direction: "toward", frameIdx: 0, returnTo: "idle" };
    inputState.hopKeyHeld = "toward";
    timers.hop.start();

    processDirectionChange("down", "up", touchState, inputState, frames, timers);
    expect(inputState.hopKeyHeld).toBe("away");
  });

  it("ends walk when releasing horizontal direction", () => {
    // Start walking right
    processDirectionChange(null, "right", touchState, inputState, frames, timers);
    expect(inputState.walkKeyHeld).toBe("right");

    // Release to deadzone (null direction)
    processDirectionChange("right", null, touchState, inputState, frames, timers);
    expect(inputState.walkKeyHeld).toBe(null);
  });

  it("handles stop horizontal when walkKeyHeld already null", () => {
    // This scenario: was hopping with diagonal, hop completed, now releasing
    // Previous direction had left component, but walkKeyHeld never set (was sliding)
    // Bunny is now idle (hop animation completed)
    inputState.bunny.animation = { kind: "idle", frameIdx: 0 };
    inputState.hopKeyHeld = null;
    inputState.walkKeyHeld = null;

    // Transition from "left" to null when not hopping and walkKeyHeld is already null
    // This can happen after diagonal hop ends and animation completes
    processDirectionChange("left", null, touchState, inputState, frames, timers);

    // walkKeyHeld should still be null, no error thrown
    expect(inputState.walkKeyHeld).toBe(null);
  });

  it("switches walk direction from left to right", () => {
    // Start walking left
    processDirectionChange(null, "left", touchState, inputState, frames, timers);
    expect(inputState.walkKeyHeld).toBe("left");
    expect(inputState.bunny.facingRight).toBe(false);

    // Drag to the right - should switch direction
    processDirectionChange("left", "right", touchState, inputState, frames, timers);
    expect(inputState.walkKeyHeld).toBe("right");
    expect(inputState.bunny.facingRight).toBe(true);
  });

  it("switches walk direction from right to left", () => {
    // Start walking right
    processDirectionChange(null, "right", touchState, inputState, frames, timers);
    expect(inputState.walkKeyHeld).toBe("right");
    expect(inputState.bunny.facingRight).toBe(true);

    // Drag to the left - should switch direction
    processDirectionChange("right", "left", touchState, inputState, frames, timers);
    expect(inputState.walkKeyHeld).toBe("left");
    expect(inputState.bunny.facingRight).toBe(false);
  });

  it("does not restart walk when returning from diagonal hop to same horizontal", () => {
    // Start walking left
    processDirectionChange(null, "left", touchState, inputState, frames, timers);
    expect(inputState.walkKeyHeld).toBe("left");

    // Go to diagonal - this starts hop, but walkKeyHeld stays "left"
    processDirectionChange("left", "up-left", touchState, inputState, frames, timers);
    expect(inputState.hopKeyHeld).toBe("away");
    expect(inputState.walkKeyHeld).toBe("left"); // Still set from before

    // Set walk animation frame to verify it doesn't reset
    inputState.bunny.animation = { kind: "walk", frameIdx: 5 };

    // Return to pure left - hop ends, walk should continue without restarting
    processDirectionChange("up-left", "left", touchState, inputState, frames, timers);

    // walkKeyHeld should still be "left", animation not reset
    expect(inputState.walkKeyHeld).toBe("left");
    expect(inputState.hopKeyHeld).toBe(null);
    expect(inputState.bunny.animation.frameIdx).toBe(5);
  });

  it("does not restart walk when returning from diagonal hop to same horizontal (right)", () => {
    // Start walking right
    processDirectionChange(null, "right", touchState, inputState, frames, timers);
    expect(inputState.walkKeyHeld).toBe("right");

    // Go to diagonal - this starts hop, but walkKeyHeld stays "right"
    processDirectionChange("right", "down-right", touchState, inputState, frames, timers);
    expect(inputState.hopKeyHeld).toBe("toward");
    expect(inputState.walkKeyHeld).toBe("right"); // Still set from before

    // Set walk animation frame to verify it doesn't reset
    inputState.bunny.animation = { kind: "walk", frameIdx: 3 };

    // Return to pure right - hop ends, walk should continue without restarting
    processDirectionChange("down-right", "right", touchState, inputState, frames, timers);

    // walkKeyHeld should still be "right", animation not reset
    expect(inputState.walkKeyHeld).toBe("right");
    expect(inputState.hopKeyHeld).toBe(null);
    expect(inputState.bunny.animation.frameIdx).toBe(3);
  });
});

describe("handleTouchEnd", () => {
  let inputState: InputState;
  let touchState: TouchState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;
  const config = DEFAULT_TOUCH_CONFIG;

  beforeEach(() => {
    vi.useFakeTimers();
    inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
    touchState = createTouchState();
    frames = createTestFrames();
    timers = createBunnyTimers(inputState.bunny, frames, {
      walk: 100, idle: 200, jump: 50, transition: 80, hop: 100,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does nothing if no joystick", () => {
    handleTouchEnd(touchState, inputState, frames, timers, Date.now(), config);
    expect(inputState.bunny.animation.kind).toBe("idle");
  });

  it("triggers jump on tap", () => {
    touchState.joystick = createJoystick(0, 0, Date.now() - 100);
    handleTouchEnd(touchState, inputState, frames, timers, Date.now(), config);
    expect(inputState.bunny.animation.kind).toBe("transition");
  });

  it("does not trigger jump on tap while hopping", () => {
    touchState.joystick = createJoystick(0, 0, Date.now() - 100);
    inputState.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };

    handleTouchEnd(touchState, inputState, frames, timers, Date.now(), config);

    // Still hopping, not jumped
    expect(inputState.bunny.animation.kind).toBe("hop");
  });

  it("ends movement on non-tap release", () => {
    touchState.joystick = createJoystick(0, -50, Date.now() - 300);
    inputState.hopKeyHeld = "away";
    inputState.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };
    timers.hop.start();

    handleTouchEnd(touchState, inputState, frames, timers, Date.now(), config);
    expect(inputState.hopKeyHeld).toBe(null);
    expect(touchState.joystick).toBe(null);
  });
});

describe("handleTouchStart", () => {
  it("creates joystick from touch", () => {
    const touchState = createTouchState();
    const touches = createMockTouchList([{ identifier: 1, clientX: 100, clientY: 200 }]);

    const result = handleTouchStart(touchState, touches, 1000);

    expect(result).toBe(true);
    expect(touchState.joystick?.anchorX).toBe(100);
    expect(touchState.joystick?.anchorY).toBe(200);
    expect(touchState.joystick?.identifier).toBe(1);
  });

  it("returns false if joystick already exists", () => {
    const touchState = createTouchState();
    touchState.joystick = createJoystick(0, 0);

    const result = handleTouchStart(touchState, createMockTouchList([{ identifier: 2, clientX: 50, clientY: 50 }]), 1000);
    expect(result).toBe(false);
  });

  it("returns false for empty touch list", () => {
    const touchState = createTouchState();
    expect(handleTouchStart(touchState, createMockTouchList([]), 1000)).toBe(false);
  });
});

describe("handleTouchMove", () => {
  let inputState: InputState;
  let touchState: TouchState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    vi.useFakeTimers();
    inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
    touchState = createTouchState();
    frames = createTestFrames();
    timers = createBunnyTimers(inputState.bunny, frames, {
      walk: 100, idle: 200, jump: 50, transition: 80, hop: 100,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns false without joystick", () => {
    const result = handleTouchMove(touchState, inputState, frames, timers, createMockTouchList([]), DEFAULT_TOUCH_CONFIG);
    expect(result).toBe(false);
  });

  it("returns false when touch identifier not found", () => {
    touchState.joystick = createJoystick(0, 0, 1000);
    // Different identifier than the joystick's (0)
    const touches = createMockTouchList([{ identifier: 99, clientX: 200, clientY: 100 }]);

    const result = handleTouchMove(touchState, inputState, frames, timers, touches, DEFAULT_TOUCH_CONFIG);
    expect(result).toBe(false);
  });

  it("updates direction on move", () => {
    touchState.joystick = createJoystick(0, 0, 1000);
    const touches = createMockTouchList([{ identifier: 0, clientX: 200, clientY: 100 }]);

    const result = handleTouchMove(touchState, inputState, frames, timers, touches, DEFAULT_TOUCH_CONFIG);

    expect(result).toBe(true);
    expect(touchState.currentDirection).toBe("right");
    expect(inputState.walkKeyHeld).toBe("right");
  });

  it("does not trigger direction change when direction unchanged", () => {
    touchState.joystick = createJoystick(0, 0, 1000);
    touchState.currentDirection = "right";
    inputState.walkKeyHeld = "right";

    // Move further right (still in same direction sector)
    const touches = createMockTouchList([{ identifier: 0, clientX: 250, clientY: 100 }]);

    const result = handleTouchMove(touchState, inputState, frames, timers, touches, DEFAULT_TOUCH_CONFIG);

    expect(result).toBe(true);
    expect(touchState.currentDirection).toBe("right");
    // walkKeyHeld unchanged, no duplicate handler calls
    expect(inputState.walkKeyHeld).toBe("right");
  });
});

describe("handleTouchEndEvent", () => {
  let inputState: InputState;
  let touchState: TouchState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    vi.useFakeTimers();
    inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
    touchState = createTouchState();
    frames = createTestFrames();
    timers = createBunnyTimers(inputState.bunny, frames, {
      walk: 100, idle: 200, jump: 50, transition: 80, hop: 100,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does nothing when joystick is null", () => {
    handleTouchEndEvent(touchState, inputState, frames, timers, createMockTouchList([]), 1000, DEFAULT_TOUCH_CONFIG);
    expect(touchState.joystick).toBe(null);
    expect(inputState.bunny.animation.kind).toBe("idle");
  });

  it("does nothing if touch still active", () => {
    touchState.joystick = createJoystick(0, 0, 1000);
    const touches = createMockTouchList([{ identifier: 0, clientX: 100, clientY: 100 }]);

    handleTouchEndEvent(touchState, inputState, frames, timers, touches, 1500, DEFAULT_TOUCH_CONFIG);
    expect(touchState.joystick).not.toBe(null);
  });

  it("ends touch when tracked touch removed", () => {
    touchState.joystick = createJoystick(0, 0, 1000);

    handleTouchEndEvent(touchState, inputState, frames, timers, createMockTouchList([]), 1500, DEFAULT_TOUCH_CONFIG);
    expect(touchState.joystick).toBe(null);
  });
});

describe("setupTouchControls integration", () => {
  let inputState: InputState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;
  let target: HTMLDivElement;

  function dispatchTouchEvent(type: string, touches: { identifier: number; clientX: number; clientY: number }[]): void {
    const touchObjs = touches.map(t => new Touch({
      identifier: t.identifier,
      target,
      clientX: t.clientX,
      clientY: t.clientY,
      pageX: t.clientX,
      pageY: t.clientY,
      screenX: t.clientX,
      screenY: t.clientY,
      radiusX: 1,
      radiusY: 1,
      rotationAngle: 0,
      force: 1,
    }));

    document.dispatchEvent(new TouchEvent(type, {
      touches: touchObjs,
      cancelable: true,
      bubbles: true,
    }));
  }

  beforeEach(() => {
    vi.useFakeTimers();
    inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
    frames = createTestFrames();
    timers = createBunnyTimers(inputState.bunny, frames, {
      walk: 100, idle: 200, jump: 50, transition: 80, hop: 100,
    });
    target = document.createElement("div");
    document.body.appendChild(target);
  });

  afterEach(() => {
    vi.useRealTimers();
    target.remove();
  });

  it("creates joystick on touchstart", () => {
    const touchState = setupTouchControls(inputState, frames, timers);

    dispatchTouchEvent("touchstart", [{ identifier: 1, clientX: 100, clientY: 200 }]);

    expect(touchState.joystick).not.toBe(null);
    expect(touchState.joystick?.anchorX).toBe(100);
  });

  it("triggers walk on touchmove", () => {
    const touchState = setupTouchControls(inputState, frames, timers);

    dispatchTouchEvent("touchstart", [{ identifier: 1, clientX: 100, clientY: 100 }]);
    dispatchTouchEvent("touchmove", [{ identifier: 1, clientX: 200, clientY: 100 }]);

    expect(touchState.currentDirection).toBe("right");
    expect(inputState.walkKeyHeld).toBe("right");
  });

  it("clears joystick on touchend", () => {
    const touchState = setupTouchControls(inputState, frames, timers);

    dispatchTouchEvent("touchstart", [{ identifier: 1, clientX: 100, clientY: 100 }]);
    vi.advanceTimersByTime(300);
    dispatchTouchEvent("touchend", []);

    expect(touchState.joystick).toBe(null);
  });

  it("clears joystick on touchcancel", () => {
    const touchState = setupTouchControls(inputState, frames, timers);

    dispatchTouchEvent("touchstart", [{ identifier: 1, clientX: 100, clientY: 100 }]);
    vi.advanceTimersByTime(300);
    dispatchTouchEvent("touchcancel", []);

    expect(touchState.joystick).toBe(null);
  });

  it("ignores second touchstart when joystick exists", () => {
    const touchState = setupTouchControls(inputState, frames, timers);

    dispatchTouchEvent("touchstart", [{ identifier: 1, clientX: 100, clientY: 100 }]);
    dispatchTouchEvent("touchstart", [{ identifier: 2, clientX: 200, clientY: 200 }]);

    // Still tracking original touch
    expect(touchState.joystick?.identifier).toBe(1);
    expect(touchState.joystick?.anchorX).toBe(100);
  });

  it("ignores touchmove with different identifier", () => {
    const touchState = setupTouchControls(inputState, frames, timers);

    dispatchTouchEvent("touchstart", [{ identifier: 1, clientX: 100, clientY: 100 }]);
    // Move with different identifier
    dispatchTouchEvent("touchmove", [{ identifier: 99, clientX: 200, clientY: 100 }]);

    // Direction unchanged (no movement processed)
    expect(touchState.currentDirection).toBe(null);
  });

  it("does not prevent default when handler returns false", () => {
    setupTouchControls(inputState, frames, timers);

    // touchmove without touchstart - handleTouchMove returns false
    const event = new TouchEvent("touchmove", {
      touches: [],
      cancelable: true,
      bubbles: true,
    });
    document.dispatchEvent(event);

    // Event was not prevented (no joystick exists)
    expect(event.defaultPrevented).toBe(false);
  });
});

describe("DEFAULT_TOUCH_CONFIG", () => {
  it("has expected values", () => {
    expect(DEFAULT_TOUCH_CONFIG.deadzone).toBe(20);
    expect(DEFAULT_TOUCH_CONFIG.tapThreshold).toBe(200);
    expect(DEFAULT_TOUCH_CONFIG.tapMaxDistance).toBe(15);
  });
});
