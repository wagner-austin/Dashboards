/**
 * Input arbiter - the single writer of effective movement intent.
 *
 * Every input source submits its own intent here. The arbiter resolves them by
 * priority, writes the winner to `state.intent`, and drives the animation
 * reducer when the effective intent actually changes. No source writes engine
 * state itself, so sources cannot silently contradict one another.
 *
 * Priority: a non-neutral "user" intent always beats "autopilot". The autopilot
 * therefore never has to be explicitly suppressed at the source - it simply
 * loses arbitration for as long as the user is holding an input.
 */
import { type BunnyFrames, type BunnyTimers } from "../entities/Bunny.js";
import { type IntentSource, type MovementIntent } from "./intent.js";
import type { InputState } from "./state.js";
/**
 * Dependencies required to arbitrate and apply intents.
 *
 * state: Engine state whose `intent` field this arbiter owns.
 * frames: Bunny animation frames.
 * timers: Bunny animation timers.
 */
export interface ArbiterDeps {
    readonly state: InputState;
    readonly frames: BunnyFrames;
    readonly timers: BunnyTimers;
}
/**
 * Resolves competing per-source intents into the effective intent.
 */
export interface InputArbiter {
    /** Record a source's current intent and apply the resolved winner. */
    readonly submit: (source: IntentSource, intent: MovementIntent) => void;
    /** Request a one-shot jump on behalf of a source. */
    readonly requestJump: (source: IntentSource) => void;
    /** Read back the intent last submitted by a source. */
    readonly intentFor: (source: IntentSource) => MovementIntent;
}
/**
 * Resolve competing intents by source priority.
 *
 * Args:
 *     user: Intent most recently submitted by keyboard or touch.
 *     autopilot: Intent most recently submitted by the autopilot.
 *
 * Returns:
 *     The user intent when it requests movement, otherwise the autopilot's.
 */
declare function resolveIntent(user: MovementIntent, autopilot: MovementIntent): MovementIntent;
/**
 * Check whether the bunny is in a state that refuses a new jump.
 *
 * Args:
 *     deps: Arbiter dependencies holding the bunny state.
 *
 * Returns:
 *     True if a jump must be ignored.
 */
declare function jumpBlocked(deps: ArbiterDeps): boolean;
/**
 * Create an input arbiter owning the effective intent of the given state.
 *
 * Args:
 *     deps: Engine state, frames, and timers to drive.
 *
 * Returns:
 *     InputArbiter with both sources starting neutral.
 */
export declare function createInputArbiter(deps: ArbiterDeps): InputArbiter;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    resolveIntent: typeof resolveIntent;
    jumpBlocked: typeof jumpBlocked;
    createInputArbiter: typeof createInputArbiter;
};
export {};
//# sourceMappingURL=arbiter.d.ts.map