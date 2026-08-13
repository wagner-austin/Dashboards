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
import { isHopping, isJumping } from "../entities/Bunny.js";
import { handleWalkKeyDown, handleWalkKeyUp, handleHopInput, handleHopRelease } from "./handlers.js";
import { isHorizontalRequested } from "./state.js";
/**
 * Apply the depth (vertical) portion of an intent change.
 *
 * Args:
 *     previous: Intent in effect before the change.
 *     next: Intent now in effect.
 *     state: Input state containing the bunny.
 *     timers: Bunny animation timers.
 */
function applyVerticalChange(previous, next, state, timers) {
    const isHorizontalHeld = () => isHorizontalRequested(state);
    const wasVertical = previous.vertical !== null;
    const isVertical = next.vertical !== null;
    if (!wasVertical && isVertical) {
        handleHopInput(state.bunny, timers, next.vertical === "up" ? "away" : "toward");
    }
    else if (wasVertical && !isVertical) {
        handleHopRelease(state.bunny, timers, isHorizontalHeld);
    }
    else if (previous.vertical === "up" && next.vertical === "down") {
        handleHopRelease(state.bunny, timers, isHorizontalHeld);
        handleHopInput(state.bunny, timers, "toward");
    }
    else if (previous.vertical === "down" && next.vertical === "up") {
        handleHopRelease(state.bunny, timers, isHorizontalHeld);
        handleHopInput(state.bunny, timers, "away");
    }
}
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
function applyHorizontalChange(previous, next, state, frames, timers) {
    const inAir = isHopping(state.bunny) || isJumping(state.bunny) || next.vertical !== null;
    if (inAir) {
        if (next.horizontal === "left") {
            state.bunny.facingRight = false;
        }
        else if (next.horizontal === "right") {
            state.bunny.facingRight = true;
        }
        return;
    }
    if (next.horizontal === "left" && previous.horizontal !== "left") {
        handleWalkKeyDown(state.bunny, frames, timers, false);
    }
    else if (next.horizontal === "right" && previous.horizontal !== "right") {
        handleWalkKeyDown(state.bunny, frames, timers, true);
    }
    else if (next.horizontal === null && previous.horizontal !== null) {
        handleWalkKeyUp(state.bunny, timers);
    }
}
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
export function applyIntentChange(previous, next, state, frames, timers) {
    applyVerticalChange(previous, next, state, timers);
    applyHorizontalChange(previous, next, state, frames, timers);
}
/** Test hooks for internal functions */
export const _test_hooks = {
    applyVerticalChange,
    applyHorizontalChange,
    applyIntentChange,
};
//# sourceMappingURL=reducer.js.map