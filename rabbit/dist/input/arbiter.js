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
import { isHopping, isJumping } from "../entities/Bunny.js";
import { handleJumpInput, isPendingJump } from "./handlers.js";
import { NEUTRAL_INTENT, intentsEqual, isNeutralIntent, } from "./intent.js";
import { applyIntentChange } from "./reducer.js";
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
function resolveIntent(user, autopilot) {
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
function jumpBlocked(deps) {
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
export function createInputArbiter(deps) {
    const submitted = {
        user: NEUTRAL_INTENT,
        autopilot: NEUTRAL_INTENT,
    };
    return {
        submit(source, intent) {
            submitted[source] = intent;
            const previous = deps.state.intent;
            const next = resolveIntent(submitted.user, submitted.autopilot);
            if (intentsEqual(previous, next)) {
                return;
            }
            deps.state.intent = next;
            applyIntentChange(previous, next, deps.state, deps.frames, deps.timers);
        },
        requestJump(source) {
            if (source === "autopilot" && !isNeutralIntent(submitted.user)) {
                return;
            }
            if (jumpBlocked(deps)) {
                return;
            }
            handleJumpInput(deps.state.bunny, deps.frames, deps.timers);
        },
        intentFor(source) {
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
//# sourceMappingURL=arbiter.js.map