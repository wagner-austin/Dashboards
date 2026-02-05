/**
 * @vitest-environment jsdom
 * Tests for keyboard input handling.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { setupKeyboardControls, type InputState } from "./Keyboard.js";
import type { BunnyFrames, BunnyTimers } from "../entities/Bunny.js";
import type { TreeSize } from "../entities/Tree.js";
import type { AnimationTimer } from "../loaders/sprites.js";

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
    tree: {
      frameIdx: 0,
      direction: 1,
      sizeIdx: 2,
      targetSizeIdx: 2,
      sizeTransitionProgress: 0,
      centerX: 200,
    },
    viewport: { width: 100, height: 50, charW: 10, charH: 20 },
    groundScrollX: 0,
  };
}

function createMockTreeSizes(): TreeSize[] {
  return [
    { width: 60, frames: ["s0"] },
    { width: 120, frames: ["m0"] },
    { width: 180, frames: ["l0"] },
  ];
}

function dispatchKeyDown(key: string, repeat = false): void {
  document.dispatchEvent(new KeyboardEvent("keydown", { key, repeat }));
}

describe("setupKeyboardControls", () => {
  let state: InputState;
  let timers: BunnyTimers;
  let frames: BunnyFrames;
  let treeSizes: TreeSize[];

  beforeEach(() => {
    state = createMockState();
    timers = createMockBunnyTimers();
    frames = createMockFrames();
    treeSizes = createMockTreeSizes();
    setupKeyboardControls(state, frames, timers, treeSizes);
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
    it("resets tree and scroll when r pressed", () => {
      state.groundScrollX = 500;
      state.tree.centerX = 50;

      dispatchKeyDown("r");

      expect(state.groundScrollX).toBe(0);
      expect(state.tree.centerX).toBe(160); // width + 60
    });

    it("responds to R key (uppercase)", () => {
      state.groundScrollX = 500;

      dispatchKeyDown("R");

      expect(state.groundScrollX).toBe(0);
    });
  });

  describe("tree zoom input", () => {
    it("zooms in with w key", () => {
      state.tree.targetSizeIdx = 1;
      dispatchKeyDown("w");
      expect(state.tree.targetSizeIdx).toBe(2);
    });

    it("zooms in with ArrowUp", () => {
      state.tree.targetSizeIdx = 0;
      dispatchKeyDown("ArrowUp");
      expect(state.tree.targetSizeIdx).toBe(1);
    });

    it("does not zoom past max", () => {
      state.tree.targetSizeIdx = 2;
      dispatchKeyDown("w");
      expect(state.tree.targetSizeIdx).toBe(2);
    });

    it("zooms out with s key", () => {
      state.tree.targetSizeIdx = 2;
      dispatchKeyDown("s");
      expect(state.tree.targetSizeIdx).toBe(1);
    });

    it("zooms out with ArrowDown", () => {
      state.tree.targetSizeIdx = 2;
      dispatchKeyDown("ArrowDown");
      expect(state.tree.targetSizeIdx).toBe(1);
    });

    it("does not zoom past min", () => {
      state.tree.targetSizeIdx = 0;
      dispatchKeyDown("s");
      expect(state.tree.targetSizeIdx).toBe(0);
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
