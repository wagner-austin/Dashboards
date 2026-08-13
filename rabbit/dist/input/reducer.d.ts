/**
 * Intent-to-animation reducer.
 *
 * The single place where a change in movement intent is translated into bunny
 * state machine calls. It knows nothing about where an intent came from, so
 * keyboard, touch, and the autopilot are guaranteed to produce identical
 * animation behaviour for identical intents.
 *
 * Callers must write the new intent to `state.intent` before invoking this,
 * because animation completion callbacks read the effective intent to decide
 * whether to settle into idle or resume walking.
 */
import { type BunnyFrames, type BunnyTimers } from "../entities/Bunny.js";
import type { MovementIntent } from "./intent.js";
import { type InputState } from "./state.js";
/**
 * Apply the depth (vertical) portion of an intent change.
 *
 * Args:
 *     previous: Intent in effect before the change.
 *     next: Intent now in effect.
 *     state: Input state containing the bunny.
 *     timers: Bunny animation timers.
 */
declare function applyVerticalChange(previous: MovementIntent, next: MovementIntent, state: InputState, timers: BunnyTimers): void;
/**
 * Apply the horizontal portion of an intent change.
 *
 * While the bunny is airborne, horizontal intent only updates facing so it
 * lands pointing the right way; it does not start or stop a walk.
 *
 * Args:
 *     previous: Intent in effect before the change.
 *     next: Intent now in effect.
 *     state: Input state containing the bunny.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 */
declare function applyHorizontalChange(previous: MovementIntent, next: MovementIntent, state: InputState, frames: BunnyFrames, timers: BunnyTimers): void;
/**
 * Drive the bunny state machine from a change in effective movement intent.
 *
 * Args:
 *     previous: Intent in effect before the change.
 *     next: Intent now in effect. Must already be written to state.intent.
 *     state: Input state containing the bunny.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 */
export declare function applyIntentChange(previous: MovementIntent, next: MovementIntent, state: InputState, frames: BunnyFrames, timers: BunnyTimers): void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    applyVerticalChange: typeof applyVerticalChange;
    applyHorizontalChange: typeof applyHorizontalChange;
    applyIntentChange: typeof applyIntentChange;
};
export {};
//# sourceMappingURL=reducer.d.ts.map