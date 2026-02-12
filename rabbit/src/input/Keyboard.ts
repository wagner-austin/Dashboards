/**
 * Keyboard input handling.
 */

import {
  isHopping,
  isJumping,
  type BunnyState,
  type BunnyFrames,
  type BunnyTimers,
} from "../entities/Bunny.js";
import type { ViewportState } from "../rendering/Viewport.js";
import type { Camera, DepthBounds } from "../world/Projection.js";
import { DEFAULT_CAMERA_Z, wrapDepth } from "../world/Projection.js";
import {
  isPendingJump,
  handleJumpInput,
  handleWalkKeyDown,
  handleWalkKeyUp,
  handleHopInput,
  handleHopRelease,
} from "./handlers.js";

/**
 * Input state containing all mutable game state.
 *
 * bunny: Bunny animation state.
 * viewport: Screen dimensions.
 * camera: Camera position.
 * depthBounds: Bounds for depth wrapping (from config).
 * hopKeyHeld: Whether W/S key is currently held (for depth movement).
 * slideKeyHeld: Whether A/D key is currently held (for horizontal slide during hop).
 * walkKeyHeld: Whether A/D key is currently held (for horizontal walk movement).
 */
export interface InputState {
  bunny: BunnyState;
  viewport: ViewportState;
  camera: Camera;
  depthBounds: DepthBounds;
  hopKeyHeld: "away" | "toward" | null;
  slideKeyHeld: "left" | "right" | null;
  walkKeyHeld: "left" | "right" | null;
}

/**
 * Setup keyboard controls for the game.
 *
 * Args:
 *     state: Mutable input state.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 */
export function setupKeyboardControls(
  state: InputState,
  bunnyFrames: BunnyFrames,
  bunnyTimers: BunnyTimers
): void {
  document.addEventListener("keydown", (e: KeyboardEvent) => {
    if (e.repeat) {
      return;
    }

    const key = e.key.toLowerCase();
    const isLeftKey = e.key === "ArrowLeft" || key === "a";
    const isRightKey = e.key === "ArrowRight" || key === "d";

    if (isLeftKey) {
      if (isHopping(state.bunny)) {
        state.slideKeyHeld = "left";
      } else {
        state.walkKeyHeld = "left";
        handleWalkKeyDown(state.bunny, bunnyFrames, bunnyTimers, false);
      }
    } else if (isRightKey) {
      if (isHopping(state.bunny)) {
        state.slideKeyHeld = "right";
      } else {
        state.walkKeyHeld = "right";
        handleWalkKeyDown(state.bunny, bunnyFrames, bunnyTimers, true);
      }
    } else if (e.key === " " && !isJumping(state.bunny) && !isPendingJump(state.bunny)) {
      handleJumpInput(state.bunny, bunnyFrames, bunnyTimers);
      e.preventDefault();
    } else if (key === "r") {
      state.camera = { x: 0, z: DEFAULT_CAMERA_Z };
    } else if (key === "w" || e.key === "ArrowUp") {
      state.hopKeyHeld = "away";
      handleHopInput(state.bunny, bunnyTimers, "away");
    } else if (key === "s" || e.key === "ArrowDown") {
      state.hopKeyHeld = "toward";
      handleHopInput(state.bunny, bunnyTimers, "toward");
    }
  });

  document.addEventListener("keyup", (e: KeyboardEvent) => {
    const key = e.key.toLowerCase();
    switch (true) {
      case key === "w":
      case e.key === "ArrowUp":
      case key === "s":
      case e.key === "ArrowDown":
        state.hopKeyHeld = null;
        state.slideKeyHeld = null;
        handleHopRelease(state.bunny, bunnyTimers);
        break;
      case key === "a":
      case e.key === "ArrowLeft":
        if (state.slideKeyHeld === "left") {
          state.slideKeyHeld = null;
        }
        if (state.walkKeyHeld === "left") {
          state.walkKeyHeld = null;
          handleWalkKeyUp(state.bunny, bunnyTimers);
        }
        break;
      case key === "d":
      case e.key === "ArrowRight":
        if (state.slideKeyHeld === "right") {
          state.slideKeyHeld = null;
        }
        if (state.walkKeyHeld === "right") {
          state.walkKeyHeld = null;
          handleWalkKeyUp(state.bunny, bunnyTimers);
        }
        break;
    }
  });
}

/** Camera Z movement speed per frame. */
const CAMERA_Z_SPEED = 0.5;

/**
 * Process camera depth movement based on hop state.
 *
 * Camera moves when bunny is hopping, with infinite wrapping at depth bounds.
 * Moving "toward" decreases Z (toward viewer).
 * Moving "away" increases Z (into scene).
 *
 * Args:
 *     state: Input state with bunny, camera, and depthBounds.
 */
export function processDepthMovement(state: InputState): void {
  const anim = state.bunny.animation;
  if (anim.kind !== "hop") {
    return;
  }

  const delta = anim.direction === "toward" ? -CAMERA_Z_SPEED : CAMERA_Z_SPEED;
  const newZ = wrapDepth(
    state.camera.z + delta,
    state.depthBounds.minZ,
    state.depthBounds.maxZ
  );

  state.camera = { ...state.camera, z: newZ };
}

/** Camera X movement speed per frame when sliding during hop */
const CAMERA_X_SPEED = 2;

/**
 * Process horizontal camera movement when sliding during hop.
 *
 * Camera only moves horizontally when bunny is hopping and A/D is held.
 *
 * Args:
 *     state: Input state with bunny, camera, and slideKeyHeld.
 */
export function processHorizontalMovement(state: InputState): void {
  if (state.bunny.animation.kind !== "hop" || state.slideKeyHeld === null) {
    return;
  }

  const direction = state.slideKeyHeld === "left" ? -1 : 1;
  state.camera = { ...state.camera, x: state.camera.x + CAMERA_X_SPEED * direction };
}

/** Camera X movement speed per frame when walking */
const WALK_SPEED = 2;

/**
 * Process horizontal camera movement while walking.
 *
 * Camera moves horizontally when bunny is walking and walkKeyHeld is set.
 *
 * Args:
 *     state: Input state with bunny, camera, and walkKeyHeld.
 */
export function processWalkMovement(state: InputState): void {
  if (state.bunny.animation.kind !== "walk" || state.walkKeyHeld === null) {
    return;
  }

  const direction = state.walkKeyHeld === "left" ? -1 : 1;
  state.camera = { ...state.camera, x: state.camera.x + WALK_SPEED * direction };
}

/** Test hooks for internal functions (re-exports handlers + local constants) */
export const _test_hooks = {
  // Re-exported from handlers.ts
  handleJumpInput,
  handleWalkKeyDown,
  handleWalkKeyUp,
  handleHopInput,
  handleHopRelease,
  isPendingJump,
  // Local to Keyboard.ts
  processDepthMovement,
  processHorizontalMovement,
  processWalkMovement,
  CAMERA_Z_SPEED,
  CAMERA_X_SPEED,
  WALK_SPEED,
};
