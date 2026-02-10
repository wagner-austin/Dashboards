/**
 * @vitest-environment jsdom
 * Tests for keyboard input handling.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { setupKeyboardControls, processZoom, _test_hooks, type InputState } from "./Keyboard.js";
import type { BunnyFrames, BunnyTimers } from "../entities/Bunny.js";
import type { AnimationTimer } from "../loaders/sprites.js";
import { createCamera } from "../world/Projection.js";

const { CAMERA_Z_SPEED, MIN_CAMERA_Z, MAX_CAMERA_Z } = _test_hooks;

function createMockTimer(): AnimationTimer {
  return {
    start: vi.fn(),
    stop: vi.fn(),
    isRunning: vi.fn().mockReturnValue(false),
  };
}

function createMockBunnyTimers(): BunnyTimers {
  return {
    walk: createMockTimer(),
    idle: createMockTimer(),
    jump: createMockTimer(),
    transition: createMockTimer(),
  };
}

function createMockFrames(): BunnyFrames {
  return {
    walkLeft: ["walkL0", "walkL1"],
    walkRight: ["walkR0", "walkR1"],
    jumpLeft: ["jumpL0"],
    jumpRight: ["jumpR0"],
    idleLeft: ["idleL0"],
    idleRight: ["idleR0"],
    walkToIdleLeft: ["transL0", "transL1", "transL2"],
    walkToIdleRight: ["transR0", "transR1", "transR2"],
  };
}

function createMockState(): InputState {
  return {
    bunny: {
      facingRight: false,
      currentAnimation: "idle",
      bunnyFrameIdx: 0,
      isJumping: false,
      jumpFrameIdx: 0,
      isWalking: false,
      pendingJump: false,
      preJumpAnimation: null,
    },
    viewport: { width: 100, height: 50, charW: 10, charH: 20 },
    camera: createCamera(),
    zoomDirection: 0,
  };
}

function dispatchKeyDown(key: string, repeat = false): void {
  document.dispatchEvent(new KeyboardEvent("keydown", { key, repeat }));
}

describe("setupKeyboardControls", () => {
  let state: InputState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;

  beforeEach(() => {
    state = createMockState();
    timers = createMockBunnyTimers();
    frames = createMockFrames();
    setupKeyboardControls(state, frames, timers);
  });

  describe("walk input", () => {
    it("starts walking left when ArrowLeft pressed from idle", () => {
      dispatchKeyDown("ArrowLeft");
      expect(state.bunny.isWalking).toBe(true);
      expect(state.bunny.facingRight).toBe(false);
    });

    it("starts walking right when ArrowRight pressed from idle", () => {
      dispatchKeyDown("ArrowRight");
      expect(state.bunny.isWalking).toBe(true);
      expect(state.bunny.facingRight).toBe(true);
    });

    it("responds to a key (lowercase)", () => {
      dispatchKeyDown("a");
      expect(state.bunny.isWalking).toBe(true);
      expect(state.bunny.facingRight).toBe(false);
    });

    it("responds to d key (lowercase)", () => {
      dispatchKeyDown("d");
      expect(state.bunny.isWalking).toBe(true);
      expect(state.bunny.facingRight).toBe(true);
    });

    it("responds to A key (uppercase/caps lock)", () => {
      dispatchKeyDown("A");
      expect(state.bunny.isWalking).toBe(true);
      expect(state.bunny.facingRight).toBe(false);
    });

    it("responds to D key (uppercase/caps lock)", () => {
      dispatchKeyDown("D");
      expect(state.bunny.isWalking).toBe(true);
      expect(state.bunny.facingRight).toBe(true);
    });

    it("stops walking when same direction pressed while walking", () => {
      state.bunny.isWalking = true;
      state.bunny.facingRight = false;
      state.bunny.currentAnimation = "walk";

      dispatchKeyDown("ArrowLeft");

      expect(state.bunny.isWalking).toBe(false);
      expect(state.bunny.currentAnimation).toBe("walk_to_idle");
    });

    it("switches direction when opposite key pressed while walking", () => {
      state.bunny.isWalking = true;
      state.bunny.facingRight = false;
      state.bunny.currentAnimation = "walk";

      dispatchKeyDown("ArrowRight");

      expect(state.bunny.isWalking).toBe(true);
      expect(state.bunny.facingRight).toBe(true);
      expect(state.bunny.currentAnimation).toBe("walk");
    });

    it("ignores repeated key events", () => {
      dispatchKeyDown("ArrowLeft", true);
      expect(state.bunny.isWalking).toBe(false); // No change
    });
  });

  describe("jump input", () => {
    it("starts transition then jump when space pressed from idle", () => {
      dispatchKeyDown(" ");
      // From idle, we start a crouch transition first
      expect(state.bunny.pendingJump).toBe(true);
      expect(state.bunny.preJumpAnimation).toBe("idle");
      expect(state.bunny.currentAnimation).toBe("idle_to_walk");
      expect(timers.transition.start).toHaveBeenCalled();
      expect(timers.idle.stop).toHaveBeenCalled();
    });

    it("starts jump immediately when space pressed while walking", () => {
      state.bunny.currentAnimation = "walk";
      state.bunny.isWalking = true;
      vi.clearAllMocks();

      dispatchKeyDown(" ");

      expect(state.bunny.isJumping).toBe(true);
      expect(state.bunny.jumpFrameIdx).toBe(0);
      expect(state.bunny.preJumpAnimation).toBe("walk");
      expect(timers.jump.start).toHaveBeenCalled();
      expect(timers.walk.stop).toHaveBeenCalled();
    });

    it("does not start jump when already jumping", () => {
      state.bunny.isJumping = true;
      vi.clearAllMocks();

      dispatchKeyDown(" ");

      expect(timers.jump.start).not.toHaveBeenCalled();
    });

    it("does not start jump when pendingJump is true", () => {
      state.bunny.pendingJump = true;
      vi.clearAllMocks();

      dispatchKeyDown(" ");

      expect(timers.jump.start).not.toHaveBeenCalled();
      expect(timers.transition.start).not.toHaveBeenCalled();
    });

    it("starts jump immediately when in transition animation", () => {
      state.bunny.currentAnimation = "walk_to_idle";
      state.bunny.isWalking = false;
      vi.clearAllMocks();

      dispatchKeyDown(" ");

      expect(state.bunny.isJumping).toBe(true);
      expect(state.bunny.preJumpAnimation).toBe("idle");
      expect(timers.transition.stop).toHaveBeenCalled();
      expect(timers.jump.start).toHaveBeenCalled();
    });

    it("uses correct transition frames when jumping from idle facing right", () => {
      state.bunny.facingRight = true;
      vi.clearAllMocks();

      dispatchKeyDown(" ");

      // Should use walkToIdleRight frames (3 frames, so bunnyFrameIdx should be 2)
      expect(state.bunny.bunnyFrameIdx).toBe(2);
      expect(state.bunny.currentAnimation).toBe("idle_to_walk");
    });

    it("sets preJumpAnimation to walk when jumping from idle_to_walk while isWalking", () => {
      state.bunny.currentAnimation = "idle_to_walk";
      state.bunny.isWalking = true;
      vi.clearAllMocks();

      dispatchKeyDown(" ");

      expect(state.bunny.isJumping).toBe(true);
      expect(state.bunny.preJumpAnimation).toBe("walk");
    });
  });

  describe("reset input", () => {
    it("resets camera position and zoom level when r pressed", () => {
      state.camera = { x: 100, z: 45 };

      dispatchKeyDown("r");

      // Camera resets to default position
      expect(state.camera.x).toBe(0);
      expect(state.camera.z).toBe(55); // DEFAULT_CAMERA_Z
    });

    it("responds to R key (uppercase)", () => {
      state.camera = { x: 100, z: 45 };

      dispatchKeyDown("R");

      expect(state.camera.x).toBe(0);
      expect(state.camera.z).toBe(55);
    });
  });

  describe("zoom direction", () => {
    it("sets zoomDirection to 1 with w key", () => {
      dispatchKeyDown("w");
      expect(state.zoomDirection).toBe(1);
    });

    it("sets zoomDirection to 1 with ArrowUp", () => {
      dispatchKeyDown("ArrowUp");
      expect(state.zoomDirection).toBe(1);
    });

    it("sets zoomDirection to -1 with s key", () => {
      dispatchKeyDown("s");
      expect(state.zoomDirection).toBe(-1);
    });

    it("sets zoomDirection to -1 with ArrowDown", () => {
      dispatchKeyDown("ArrowDown");
      expect(state.zoomDirection).toBe(-1);
    });

    it("clears zoomDirection on w keyup", () => {
      dispatchKeyDown("w");
      expect(state.zoomDirection).toBe(1);
      document.dispatchEvent(new KeyboardEvent("keyup", { key: "w" }));
      expect(state.zoomDirection).toBe(0);
    });

    it("clears zoomDirection on ArrowUp keyup", () => {
      dispatchKeyDown("ArrowUp");
      expect(state.zoomDirection).toBe(1);
      document.dispatchEvent(new KeyboardEvent("keyup", { key: "ArrowUp" }));
      expect(state.zoomDirection).toBe(0);
    });

    it("clears zoomDirection on s keyup", () => {
      dispatchKeyDown("s");
      expect(state.zoomDirection).toBe(-1);
      document.dispatchEvent(new KeyboardEvent("keyup", { key: "s" }));
      expect(state.zoomDirection).toBe(0);
    });

    it("clears zoomDirection on ArrowDown keyup", () => {
      dispatchKeyDown("ArrowDown");
      expect(state.zoomDirection).toBe(-1);
      document.dispatchEvent(new KeyboardEvent("keyup", { key: "ArrowDown" }));
      expect(state.zoomDirection).toBe(0);
    });

    it("does not clear zoomDirection on unrelated keyup", () => {
      dispatchKeyDown("w");
      expect(state.zoomDirection).toBe(1);
      document.dispatchEvent(new KeyboardEvent("keyup", { key: "a" }));
      expect(state.zoomDirection).toBe(1); // Still held
    });
  });

  describe("transition handling", () => {
    it("starts idle_to_walk transition from idle", () => {
      state.bunny.currentAnimation = "idle";
      dispatchKeyDown("ArrowRight");

      expect(state.bunny.currentAnimation).toBe("idle_to_walk");
      expect(state.bunny.bunnyFrameIdx).toBe(2); // Last frame of transition
      expect(timers.idle.stop).toHaveBeenCalled();
      expect(timers.transition.start).toHaveBeenCalled();
    });

    it("interrupts walk_to_idle transition when switching direction", () => {
      state.bunny.currentAnimation = "walk_to_idle";
      state.bunny.isWalking = false;

      dispatchKeyDown("ArrowRight");

      expect(state.bunny.currentAnimation).toBe("walk");
      expect(timers.transition.stop).toHaveBeenCalled();
      expect(timers.walk.start).toHaveBeenCalled();
    });
  });
});

describe("processZoom", () => {
  it("decreases camera.z when zoomDirection is 1 (zoom in)", () => {
    const state = createMockState();
    const initialZ = state.camera.z;
    state.zoomDirection = 1;

    processZoom(state);

    expect(state.camera.z).toBe(initialZ - CAMERA_Z_SPEED);
  });

  it("increases camera.z when zoomDirection is -1 (zoom out)", () => {
    const state = createMockState();
    const initialZ = state.camera.z;
    state.zoomDirection = -1;

    processZoom(state);

    expect(state.camera.z).toBe(initialZ + CAMERA_Z_SPEED);
  });

  it("does nothing when zoomDirection is 0", () => {
    const state = createMockState();
    const initialZ = state.camera.z;
    state.zoomDirection = 0;

    processZoom(state);

    expect(state.camera.z).toBe(initialZ);
  });

  it("clamps camera.z to MIN_CAMERA_Z when zooming in", () => {
    const state = createMockState();
    state.camera = { x: state.camera.x, z: MIN_CAMERA_Z };
    state.zoomDirection = 1;

    processZoom(state);

    expect(state.camera.z).toBe(MIN_CAMERA_Z);
  });

  it("clamps camera.z to MAX_CAMERA_Z when zooming out", () => {
    const state = createMockState();
    state.camera = { x: state.camera.x, z: MAX_CAMERA_Z };
    state.zoomDirection = -1;

    processZoom(state);

    expect(state.camera.z).toBe(MAX_CAMERA_Z);
  });

  it("does nothing for invalid zoomDirection value of 2", () => {
    const state = createMockState();
    const initialZ = state.camera.z;
    state.zoomDirection = 2;

    processZoom(state);

    expect(state.camera.z).toBe(initialZ);
  });

  it("preserves camera.x when zooming", () => {
    const state = createMockState();
    state.camera = { x: 100, z: 55 };
    state.zoomDirection = 1;

    processZoom(state);

    expect(state.camera.x).toBe(100);
  });

  it("allows continuous zoom across multiple calls", () => {
    const state = createMockState();
    state.camera = { x: 0, z: 55 };
    state.zoomDirection = 1;

    processZoom(state);
    processZoom(state);
    processZoom(state);

    expect(state.camera.z).toBe(55 - CAMERA_Z_SPEED * 3);
  });

  it("stops at MIN_CAMERA_Z after multiple zoom in calls", () => {
    const state = createMockState();
    state.camera = { x: 0, z: MIN_CAMERA_Z + 1 };
    state.zoomDirection = 1;

    processZoom(state);
    processZoom(state);
    processZoom(state);

    expect(state.camera.z).toBe(MIN_CAMERA_Z);
  });

  it("stops at MAX_CAMERA_Z after multiple zoom out calls", () => {
    const state = createMockState();
    state.camera = { x: 0, z: MAX_CAMERA_Z - 1 };
    state.zoomDirection = -1;

    processZoom(state);
    processZoom(state);
    processZoom(state);

    expect(state.camera.z).toBe(MAX_CAMERA_Z);
  });
});
