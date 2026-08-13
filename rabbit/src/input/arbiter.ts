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

import { isHopping, isJumping, type BunnyFrames, type BunnyTimers } from "../entities/Bunny.js";
import { handleJumpInput, isPendingJump } from "./handlers.js";
import {
  NEUTRAL_INTENT,
  intentsEqual,
  isNeutralIntent,
  type IntentSource,
  type MovementIntent,
} from "./intent.js";
import { applyIntentChange } from "./reducer.js";
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
function resolveIntent(user: MovementIntent, autopilot: MovementIntent): MovementIntent {
  return isNeutralIntent(user) ? autopilot : user;
}

/**
 * Check whether the bunny is in a state that refuses a new jump.
 *
 * Args:
 *     deps: Arbiter dependencies holding the bunny state.
 *
 * Returns:
 *     True if a jump must be ignored.
 */
function jumpBlocked(deps: ArbiterDeps): boolean {
  const bunny = deps.state.bunny;
  return isJumping(bunny) || isPendingJump(bunny) || isHopping(bunny);
}

/**
 * Create an input arbiter owning the effective intent of the given state.
 *
 * Args:
 *     deps: Engine state, frames, and timers to drive.
 *
 * Returns:
 *     InputArbiter with both sources starting neutral.
 */
export function createInputArbiter(deps: ArbiterDeps): InputArbiter {
  const submitted: Record<IntentSource, MovementIntent> = {
    user: NEUTRAL_INTENT,
    autopilot: NEUTRAL_INTENT,
  };

  return {
    submit(source: IntentSource, intent: MovementIntent): void {
      submitted[source] = intent;

      const previous = deps.state.intent;
      const next = resolveIntent(submitted.user, submitted.autopilot);

      if (intentsEqual(previous, next)) {
        return;
      }

      deps.state.intent = next;
      applyIntentChange(previous, next, deps.state, deps.frames, deps.timers);
    },

    requestJump(source: IntentSource): void {
      if (source === "autopilot" && !isNeutralIntent(submitted.user)) {
        return;
      }
      if (jumpBlocked(deps)) {
        return;
      }
      handleJumpInput(deps.state.bunny, deps.frames, deps.timers);
    },

    intentFor(source: IntentSource): MovementIntent {
      return submitted[source];
    },
  };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  resolveIntent,
  jumpBlocked,
  createInputArbiter,
};
