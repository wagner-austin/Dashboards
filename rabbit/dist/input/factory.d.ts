/**
 * Input system factory.
 *
 * Builds the focused services of the input layer and wires them together:
 * arbiter, idle tracker, autopilot, keyboard, and touch. Callers get one
 * `update` to call per frame and never see the internal wiring, so the layer
 * can grow another source without changing the render loop.
 */
import type { BunnyFrames, BunnyTimers } from "../entities/Bunny.js";
import { type ActivityTracker } from "./activity.js";
import { type InputArbiter } from "./arbiter.js";
import type { RandomSource } from "./Autopilot.js";
import { type AutopilotController } from "./controller.js";
import { type KeyboardEventSource, type KeyboardKeys } from "./Keyboard.js";
import { type CameraSpeeds } from "./movement.js";
import type { InputState } from "./state.js";
import { type TouchConfig, type TouchEventSource, type TouchState } from "./Touch.js";
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
 * speeds: Camera pan and depth speeds, in world units per second.
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
    readonly speeds: CameraSpeeds;
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
export declare function createInputSystem(deps: InputSystemDeps): InputSystem;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createInputSystem: typeof createInputSystem;
};
//# sourceMappingURL=factory.d.ts.map