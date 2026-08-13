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
import { NEUTRAL_INTENT, createIntent, facingToDirection, reverseHorizontal, } from "./intent.js";
/** The stood-down autopilot state. */
export const DORMANT_STATE = { kind: "dormant" };
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
function randomRange(random, min, max) {
    return min + random() * (max - min);
}
/**
 * Derive the movement intent implied by an autopilot state.
 *
 * Args:
 *     state: Autopilot state to translate.
 *
 * Returns:
 *     The intent the state requests.
 */
function intentOf(state) {
    switch (state.kind) {
        case "dormant":
            return NEUTRAL_INTENT;
        case "pause":
            return NEUTRAL_INTENT;
        case "walk":
            return createIntent(state.direction, null);
        case "hop":
            return createIntent(null, state.direction);
    }
}
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
function withRemaining(state, remaining) {
    switch (state.kind) {
        case "pause":
            return { kind: "pause", remaining };
        case "walk":
            return { kind: "walk", direction: state.direction, remaining };
        case "hop":
            return { kind: "hop", direction: state.direction, remaining };
    }
}
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
function beginPause(config, random) {
    return { kind: "pause", remaining: randomRange(random, config.minPause, config.maxPause) };
}
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
function chooseWalkDirection(facingRight, config, random) {
    const current = facingToDirection(facingRight);
    return random() < config.turnChance ? reverseHorizontal(current) : current;
}
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
function beginLeg(facingRight, config, random) {
    const remaining = randomRange(random, config.minLeg, config.maxLeg);
    if (random() < config.hopChance) {
        const direction = random() < 0.5 ? "up" : "down";
        return { kind: "hop", direction, remaining };
    }
    return { kind: "walk", direction: chooseWalkDirection(facingRight, config, random), remaining };
}
/**
 * Build an output that requests no jump.
 *
 * Args:
 *     state: Autopilot state for the next frame.
 *
 * Returns:
 *     AutopilotOutput carrying the state's implied intent.
 */
function outputOf(state) {
    return { state, intent: intentOf(state), jump: false };
}
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
function endLeg(state, config, random) {
    const jump = state.kind === "walk" && random() < config.jumpChance;
    return { state: beginPause(config, random), intent: NEUTRAL_INTENT, jump };
}
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
export function stepAutopilot(state, input, config, random) {
    if (!config.enabled || input.idleSeconds < config.idleDelay) {
        return outputOf(DORMANT_STATE);
    }
    if (state.kind === "dormant") {
        return outputOf(beginLeg(input.facingRight, config, random));
    }
    const remaining = state.remaining - input.deltaTime;
    if (remaining > 0) {
        return outputOf(withRemaining(state, remaining));
    }
    if (state.kind === "pause") {
        return outputOf(beginLeg(input.facingRight, config, random));
    }
    return endLeg(state, config, random);
}
/** Test hooks for internal functions */
export const _test_hooks = {
    randomRange,
    intentOf,
    withRemaining,
    beginPause,
    chooseWalkDirection,
    beginLeg,
    outputOf,
    endLeg,
    stepAutopilot,
    DORMANT_STATE,
};
//# sourceMappingURL=Autopilot.js.map