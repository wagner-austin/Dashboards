/**
 * Autopilot - the supervisory state machine that plays the game when nobody
 * else is.
 *
 * This is the upper level of a two-level hierarchy. The autopilot decides what
 * the bunny should *want* (a MovementIntent plus the occasional one-shot jump);
 * the bunny's own animation state machine decides how that want is performed.
 * The two levels only ever meet at the intent boundary, so neither can reach
 * into the other's states.
 *
 * `stepAutopilot` is pure: same state, input, config, and random draws in,
 * same state and intent out. All mutation lives in the controller that drives
 * it, which keeps the wander logic testable with real arithmetic rather than
 * timers or stand-in objects.
 */
import { type HorizontalDirection, type MovementIntent, type VerticalDirection } from "./intent.js";
import type { AutorunConfig } from "./validation.js";
/** Autopilot is standing down because the user is present. */
export interface DormantState {
    readonly kind: "dormant";
}
/** Autopilot is idling between movement legs. */
export interface PauseState {
    readonly kind: "pause";
    readonly remaining: number;
}
/** Autopilot is walking a leg in one direction. */
export interface WalkState {
    readonly kind: "walk";
    readonly direction: HorizontalDirection;
    readonly remaining: number;
}
/** Autopilot is hopping a leg into or out of depth. */
export interface HopState {
    readonly kind: "hop";
    readonly direction: VerticalDirection;
    readonly remaining: number;
}
/** Autopilot state, timed phases plus the stood-down state. */
export type AutopilotState = DormantState | PauseState | WalkState | HopState;
/** Autopilot states that count down. */
export type TimedState = PauseState | WalkState | HopState;
/** Source of the random draws that shape wandering. */
export type RandomSource = () => number;
/**
 * Per-frame input to the autopilot.
 *
 * deltaTime: Seconds elapsed since the previous frame.
 * idleSeconds: Seconds since the user last acted.
 * facingRight: Direction the bunny currently faces.
 */
export interface AutopilotInput {
    readonly deltaTime: number;
    readonly idleSeconds: number;
    readonly facingRight: boolean;
}
/**
 * Result of stepping the autopilot one frame.
 *
 * state: Autopilot state for the next frame.
 * intent: Movement the autopilot wants this frame.
 * jump: Whether a one-shot jump should fire this frame.
 */
export interface AutopilotOutput {
    readonly state: AutopilotState;
    readonly intent: MovementIntent;
    readonly jump: boolean;
}
/** The stood-down autopilot state. */
export declare const DORMANT_STATE: DormantState;
/**
 * Draw a value uniformly from an inclusive range.
 *
 * Args:
 *     random: Source of draws in [0, 1).
 *     min: Lower bound.
 *     max: Upper bound.
 *
 * Returns:
 *     A value in [min, max).
 */
declare function randomRange(random: RandomSource, min: number, max: number): number;
/**
 * Derive the movement intent implied by an autopilot state.
 *
 * Args:
 *     state: Autopilot state to translate.
 *
 * Returns:
 *     The intent the state requests.
 */
declare function intentOf(state: AutopilotState): MovementIntent;
/**
 * Rebuild a timed state with a new remaining duration.
 *
 * Args:
 *     state: Timed state to copy.
 *     remaining: New remaining duration in seconds.
 *
 * Returns:
 *     A new state of the same kind.
 */
declare function withRemaining(state: TimedState, remaining: number): TimedState;
/**
 * Start an idle pause between movement legs.
 *
 * Consumes one random draw: the pause duration.
 *
 * Args:
 *     config: Autorun tuning values.
 *     random: Source of draws in [0, 1).
 *
 * Returns:
 *     A new pause state.
 */
declare function beginPause(config: AutorunConfig, random: RandomSource): PauseState;
/**
 * Choose the direction of the next walk leg.
 *
 * Consumes one random draw: the turn roll.
 *
 * Args:
 *     facingRight: Direction the bunny currently faces.
 *     config: Autorun tuning values.
 *     random: Source of draws in [0, 1).
 *
 * Returns:
 *     The direction to walk.
 */
declare function chooseWalkDirection(facingRight: boolean, config: AutorunConfig, random: RandomSource): HorizontalDirection;
/**
 * Start a movement leg, either a depth hop or a walk.
 *
 * Consumes three random draws in order: leg duration, the hop-versus-walk
 * roll, then either the hop direction roll or the turn roll.
 *
 * Args:
 *     facingRight: Direction the bunny currently faces.
 *     config: Autorun tuning values.
 *     random: Source of draws in [0, 1).
 *
 * Returns:
 *     A new walk or hop state.
 */
declare function beginLeg(facingRight: boolean, config: AutorunConfig, random: RandomSource): WalkState | HopState;
/**
 * Build an output that requests no jump.
 *
 * Args:
 *     state: Autopilot state for the next frame.
 *
 * Returns:
 *     AutopilotOutput carrying the state's implied intent.
 */
declare function outputOf(state: AutopilotState): AutopilotOutput;
/**
 * Finish a movement leg and drop into a pause.
 *
 * A walk leg may end with a jump; a hop leg never does, because the bunny is
 * already airborne. Consumes the jump roll only for walk legs.
 *
 * Args:
 *     state: The leg that just finished.
 *     config: Autorun tuning values.
 *     random: Source of draws in [0, 1).
 *
 * Returns:
 *     AutopilotOutput entering a pause, possibly requesting a jump.
 */
declare function endLeg(state: WalkState | HopState, config: AutorunConfig, random: RandomSource): AutopilotOutput;
/**
 * Advance the autopilot by one frame.
 *
 * Stands down whenever autorun is disabled or the user has acted more recently
 * than the configured idle delay. Otherwise counts down the current phase and
 * picks the next one when it expires.
 *
 * Args:
 *     state: Autopilot state from the previous frame.
 *     input: Frame delta, user idle time, and current facing.
 *     config: Autorun tuning values.
 *     random: Source of draws in [0, 1).
 *
 * Returns:
 *     The next state, the intent it requests, and whether to jump.
 */
export declare function stepAutopilot(state: AutopilotState, input: AutopilotInput, config: AutorunConfig, random: RandomSource): AutopilotOutput;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    randomRange: typeof randomRange;
    intentOf: typeof intentOf;
    withRemaining: typeof withRemaining;
    beginPause: typeof beginPause;
    chooseWalkDirection: typeof chooseWalkDirection;
    beginLeg: typeof beginLeg;
    outputOf: typeof outputOf;
    endLeg: typeof endLeg;
    stepAutopilot: typeof stepAutopilot;
    DORMANT_STATE: DormantState;
};
export {};
//# sourceMappingURL=Autopilot.d.ts.map