/**
 * Keyboard input handling.
 */

import type { BunnyState, BunnyFrames, BunnyTimers } from "../entities/Bunny.js";
import type { ViewportState } from "../rendering/Viewport.js";
import type { Camera } from "../world/Projection.js";
import { DEFAULT_CAMERA_Z } from "../world/Projection.js";

/**
 * Input state containing all mutable game state.
 *
 * bunny: Bunny animation state.
 * viewport: Screen dimensions.
 * camera: Camera position.
 * depthDirection: Camera Z movement direction (1=forward, -1=backward, 0=none).
 */
export interface InputState {
  bunny: BunnyState;
  viewport: ViewportState;
  camera: Camera;
  depthDirection: number;
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
      handleWalkInput(state.bunny, bunnyFrames, bunnyTimers, false);
    } else if (isRightKey) {
      handleWalkInput(state.bunny, bunnyFrames, bunnyTimers, true);
    } else if (e.key === " " && !state.bunny.isJumping && !state.bunny.pendingJump) {
      handleJumpInput(state.bunny, bunnyFrames, bunnyTimers);
      e.preventDefault();
    } else if (key === "r") {
      // Reset scene: camera position
      state.camera = { x: 0, z: DEFAULT_CAMERA_Z };
    } else if (key === "w" || e.key === "ArrowUp") {
      // Move camera into scene (rabbit hops away, trees come toward us)
      state.depthDirection = -1;
    } else if (key === "s" || e.key === "ArrowDown") {
      // Move camera out of scene (rabbit hops toward us)
      state.depthDirection = 1;
    }
  });

  document.addEventListener("keyup", (e: KeyboardEvent) => {
    const key = e.key.toLowerCase();
    if (key === "w" || e.key === "ArrowUp" || key === "s" || e.key === "ArrowDown") {
      state.depthDirection = 0;
    }
  });
}

/** Camera Z movement speed per frame */
const CAMERA_Z_SPEED = 0.5;

/** Minimum camera Z (closest to scene) */
const MIN_CAMERA_Z = -500;

/** Maximum camera Z (farthest from scene) */
const MAX_CAMERA_Z = 500;

/**
 * Process camera depth movement based on held key direction.
 *
 * Moves camera through the 3D scene based on depthDirection:
 * W/ArrowUp (depthDirection=-1): Move into scene, increases Z, zoom in effect.
 * S/ArrowDown (depthDirection=1): Move out of scene, decreases Z, zoom out effect.
 * Entities resize automatically via 3D perspective projection.
 *
 * Args:
 *     state: Input state with depthDirection and camera.
 */
export function processDepthMovement(state: InputState): void {
  if (state.depthDirection === 0) {
    return;
  }

  let newZ = state.camera.z;

  if (state.depthDirection === 1) {
    // S key: Move out of scene (decrease Z, zoom out)
    newZ = Math.max(state.camera.z - CAMERA_Z_SPEED, MIN_CAMERA_Z);
  } else if (state.depthDirection === -1) {
    // W key: Move into scene (increase Z, zoom in)
    newZ = Math.min(state.camera.z + CAMERA_Z_SPEED, MAX_CAMERA_Z);
  }

  state.camera = { ...state.camera, z: newZ };
}

/**
 * Handle jump input.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 */
function handleJumpInput(
  bunny: BunnyState,
  frames: BunnyFrames,
  timers: BunnyTimers
): void {
  const wasIdle = bunny.currentAnimation === "idle";
  const wasWalking = bunny.currentAnimation === "walk";

  if (wasIdle) {
    bunny.preJumpAnimation = "idle";
    bunny.pendingJump = true;
    timers.idle.stop();
    const transitionFrames = bunny.facingRight
      ? frames.walkToIdleRight
      : frames.walkToIdleLeft;
    bunny.currentAnimation = "idle_to_walk";
    bunny.bunnyFrameIdx = transitionFrames.length - 1;
    timers.transition.start();
  } else if (wasWalking) {
    bunny.preJumpAnimation = "walk";
    bunny.isJumping = true;
    bunny.jumpFrameIdx = 0;
    timers.walk.stop();
    timers.jump.start();
  } else {
    bunny.preJumpAnimation = bunny.isWalking ? "walk" : "idle";
    bunny.isJumping = true;
    bunny.jumpFrameIdx = 0;
    timers.transition.stop();
    timers.jump.start();
  }
}

/**
 * Handle walk input.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 *     goingRight: Direction of movement.
 */
function handleWalkInput(
  bunny: BunnyState,
  frames: BunnyFrames,
  timers: BunnyTimers,
  goingRight: boolean
): void {
  const sameDirection = bunny.facingRight === goingRight;

  if (bunny.isWalking && sameDirection && bunny.currentAnimation === "walk") {
    bunny.isWalking = false;
    timers.walk.stop();
    bunny.currentAnimation = "walk_to_idle";
    bunny.bunnyFrameIdx = 0;
    timers.transition.start();
  } else {
    const wasIdle = bunny.currentAnimation === "idle";
    const wasInTransition =
      bunny.currentAnimation === "walk_to_idle" ||
      bunny.currentAnimation === "idle_to_walk";
    bunny.facingRight = goingRight;
    bunny.isWalking = true;

    if (wasIdle) {
      timers.idle.stop();
      const transitionFrames = goingRight
        ? frames.walkToIdleRight
        : frames.walkToIdleLeft;
      bunny.currentAnimation = "idle_to_walk";
      bunny.bunnyFrameIdx = transitionFrames.length - 1;
      timers.transition.start();
    } else {
      if (wasInTransition) {
        timers.transition.stop();
      }
      bunny.currentAnimation = "walk";
      bunny.bunnyFrameIdx = 0;
      timers.walk.start();
    }
  }
}

/** Test hooks for internal functions */
export const _test_hooks = {
  handleJumpInput,
  handleWalkInput,
  processDepthMovement,
  CAMERA_Z_SPEED,
  MIN_CAMERA_Z,
  MAX_CAMERA_Z,
};
