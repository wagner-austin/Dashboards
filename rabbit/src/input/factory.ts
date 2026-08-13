/**
 * Input system factory.
 *
 * Builds the focused services of the input layer and wires them together:
 * arbiter, idle tracker, autopilot, keyboard, and touch. Callers get one
 * `update` to call per frame and never see the internal wiring, so the layer
 * can grow another source without changing the render loop.
 */

import type { BunnyFrames, BunnyTimers } from "../entities/Bunny.js";
import { createActivityTracker, type ActivityTracker } from "./activity.js";
import { createInputArbiter, type InputArbiter } from "./arbiter.js";
import type { RandomSource } from "./Autopilot.js";
import { createAutopilotController, type AutopilotController } from "./controller.js";
import {
  setupKeyboardControls,
  type KeyboardEventSource,
  type KeyboardKeys,
} from "./Keyboard.js";
import { processDepthMovement, processHorizontalMovement } from "./movement.js";
import type { InputState } from "./state.js";
import {
  setupTouchControls,
  type TouchConfig,
  type TouchEventSource,
  type TouchState,
} from "./Touch.js";
import type { AutorunConfig } from "./validation.js";

/**
 * Dependencies required to build the input system.
 *
 * state: Engine state the input layer reads and drives.
 * frames: Bunny animation frames.
 * timers: Bunny animation timers.
 * autorun: Autopilot tuning values.
 * random: Source of draws in [0, 1) shaping the autopilot wander.
 * keyboardEvents: Event target for keyboard listeners.
 * touchEvents: Event target and clock for touch listeners.
 * touch: Joystick tuning values.
 */
export interface InputSystemDeps {
  readonly state: InputState;
  readonly frames: BunnyFrames;
  readonly timers: BunnyTimers;
  readonly autorun: AutorunConfig;
  readonly random: RandomSource;
  readonly keyboardEvents: KeyboardEventSource;
  readonly touchEvents: TouchEventSource;
  readonly touch: TouchConfig;
}

/**
 * The assembled input layer.
 *
 * arbiter: Resolver and single writer of effective intent.
 * activity: Idle timer shared by the sources and the autopilot.
 * autopilot: Supervisory wander controller.
 * keys: Keyboard held-key model.
 * touchState: Joystick state.
 * update: Advances the autopilot and integrates camera movement.
 */
export interface InputSystem {
  readonly arbiter: InputArbiter;
  readonly activity: ActivityTracker;
  readonly autopilot: AutopilotController;
  readonly keys: KeyboardKeys;
  readonly touchState: TouchState;
  readonly update: (deltaTime: number) => void;
}

/**
 * Build and wire the input layer.
 *
 * Args:
 *     deps: Engine state, animation data, configuration, and event targets.
 *
 * Returns:
 *     InputSystem with keyboard and touch listeners already bound.
 */
export function createInputSystem(deps: InputSystemDeps): InputSystem {
  const arbiter = createInputArbiter({
    state: deps.state,
    frames: deps.frames,
    timers: deps.timers,
  });

  const activity = createActivityTracker();

  const autopilot = createAutopilotController({
    arbiter,
    activity,
    state: deps.state,
    config: deps.autorun,
    random: deps.random,
  });

  const keys = setupKeyboardControls({
    state: deps.state,
    arbiter,
    activity,
    events: deps.keyboardEvents,
  });

  const touchState = setupTouchControls({
    arbiter,
    activity,
    events: deps.touchEvents,
    config: deps.touch,
  });

  return {
    arbiter,
    activity,
    autopilot,
    keys,
    touchState,
    update(deltaTime: number): void {
      autopilot.update(deltaTime);
      processDepthMovement(deps.state, deltaTime);
      processHorizontalMovement(deps.state, deltaTime);
    },
  };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  createInputSystem,
};
