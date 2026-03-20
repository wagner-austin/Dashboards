/**
 * Shared input handlers for keyboard and touch.
 *
 * These handlers process input actions and mutate bunny animation state.
 * Both keyboard and touch input sources use these same handlers to ensure
 * consistent behavior and a single source of truth.
 */
import { isHopping, isJumping, } from "../entities/Bunny.js";
/**
 * Check if bunny has a pending jump.
 *
 * Args:
 *     bunny: Bunny state.
 *
 * Returns:
 *     True if in transition with pending jump action.
 */
export function isPendingJump(bunny) {
    return bunny.animation.kind === "transition" && bunny.animation.pendingAction === "jump";
}
/**
 * Handle jump input.
 *
 * Transitions bunny to jump animation from various states:
 * - From idle: starts transition with pending jump
 * - From walk: immediate jump
 * - From transition: interrupt and jump
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 */
export function handleJumpInput(bunny, frames, timers) {
    const anim = bunny.animation;
    if (anim.kind === "idle") {
        timers.idle.stop();
        const transitionFrames = bunny.facingRight
            ? frames.walkToIdleRight
            : frames.walkToIdleLeft;
        bunny.animation = {
            kind: "transition",
            type: "idle_to_walk",
            frameIdx: transitionFrames.length - 1,
            pendingAction: "jump",
            returnTo: "idle",
        };
        timers.transition.start();
    }
    else if (anim.kind === "walk") {
        timers.walk.stop();
        bunny.animation = { kind: "jump", frameIdx: 0 };
        timers.jump.start();
    }
    else if (anim.kind === "transition") {
        timers.transition.stop();
        bunny.animation = { kind: "jump", frameIdx: 0 };
        timers.jump.start();
    }
}
/**
 * Handle walk key down (start walking).
 *
 * Starts walking animation in the specified direction.
 * If already walking in a different direction, switches direction.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 *     goingRight: Direction of movement.
 */
export function handleWalkKeyDown(bunny, frames, timers, goingRight) {
    const anim = bunny.animation;
    if (anim.kind === "idle") {
        bunny.facingRight = goingRight;
        timers.idle.stop();
        const transitionFrames = goingRight
            ? frames.walkToIdleRight
            : frames.walkToIdleLeft;
        bunny.animation = {
            kind: "transition",
            type: "idle_to_walk",
            frameIdx: transitionFrames.length - 1,
            pendingAction: "walk",
            returnTo: "idle",
        };
        timers.transition.start();
    }
    else if (anim.kind === "transition") {
        bunny.facingRight = goingRight;
        timers.transition.stop();
        bunny.animation = { kind: "walk", frameIdx: 0 };
        timers.walk.start();
    }
    else if (anim.kind === "walk") {
        // Already walking - just switch direction if needed
        bunny.facingRight = goingRight;
        bunny.animation.frameIdx = 0;
    }
}
/**
 * Handle walk key up (stop walking).
 *
 * Transitions from walking to idle when the walk key is released.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     timers: Bunny animation timers.
 */
export function handleWalkKeyUp(bunny, timers) {
    const anim = bunny.animation;
    if (anim.kind === "walk") {
        timers.walk.stop();
        bunny.animation = {
            kind: "transition",
            type: "walk_to_idle",
            frameIdx: 0,
            pendingAction: null,
            returnTo: "idle",
        };
        timers.transition.start();
    }
    else if (anim.kind === "transition" && anim.type === "idle_to_walk") {
        // Cancel the transition to walk
        timers.transition.stop();
        bunny.animation = { kind: "idle", frameIdx: 0 };
        timers.idle.start();
    }
}
/**
 * Handle hop input (W/S key or touch up/down).
 *
 * Starts the animation sequence for hopping into depth (away) or out (toward).
 * From idle: idle -> walk_to_turn -> hop (loop)
 * From walk: walk -> walk_to_turn -> hop (loop)
 * From transition: updates pending action
 *
 * Does nothing if already jumping or hopping.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     timers: Bunny animation timers.
 *     direction: "away" for up/W, "toward" for down/S.
 */
export function handleHopInput(bunny, timers, direction) {
    if (isJumping(bunny) || isHopping(bunny)) {
        return;
    }
    const anim = bunny.animation;
    const pendingAction = direction === "away" ? "hop_away" : "hop_toward";
    const turnType = direction === "away" ? "walk_to_turn_away" : "walk_to_turn_toward";
    switch (anim.kind) {
        case "idle":
            timers.idle.stop();
            bunny.animation = {
                kind: "transition",
                type: turnType,
                frameIdx: 0,
                pendingAction: null,
                returnTo: "idle",
            };
            timers.transition.start();
            break;
        case "walk":
            timers.walk.stop();
            bunny.animation = {
                kind: "transition",
                type: turnType,
                frameIdx: 0,
                pendingAction: null,
                returnTo: "walk",
            };
            timers.transition.start();
            break;
        case "transition":
            bunny.animation = {
                ...anim,
                pendingAction,
            };
            break;
    }
}
/**
 * Handle hop release (W/S key or touch released).
 *
 * Stops the hopping animation and checks current input to decide next state.
 * If released during transition, cancels and checks current input.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     timers: Bunny animation timers.
 *     isHorizontalHeld: Callback to check current horizontal input.
 */
export function handleHopRelease(bunny, timers, isHorizontalHeld) {
    const anim = bunny.animation;
    // If in transition, check if it's a hop-related transition
    if (anim.kind === "transition") {
        // Cancel turn transitions (they're specifically for hopping)
        if (anim.type === "walk_to_turn_away" || anim.type === "walk_to_turn_toward") {
            timers.transition.stop();
            if (isHorizontalHeld()) {
                bunny.animation = { kind: "walk", frameIdx: 0 };
                timers.walk.start();
            }
            else {
                bunny.animation = { kind: "idle", frameIdx: 0 };
                timers.idle.start();
            }
            return;
        }
        // Clear hop pendingAction from idle_to_walk transitions, let walk happen
        if (anim.type === "idle_to_walk" && (anim.pendingAction === "hop_away" || anim.pendingAction === "hop_toward")) {
            bunny.animation = {
                kind: "transition",
                type: "idle_to_walk",
                frameIdx: anim.frameIdx,
                pendingAction: null,
                returnTo: anim.returnTo,
            };
        }
        return;
    }
    if (anim.kind !== "hop") {
        return;
    }
    timers.hop.stop();
    if (isHorizontalHeld()) {
        bunny.animation = { kind: "walk", frameIdx: 0 };
        timers.walk.start();
    }
    else {
        bunny.animation = { kind: "idle", frameIdx: 0 };
        timers.idle.start();
    }
}
/** Test hooks for internal functions */
export const _test_hooks = {
    isPendingJump,
    handleJumpInput,
    handleWalkKeyDown,
    handleWalkKeyUp,
    handleHopInput,
    handleHopRelease,
};
//# sourceMappingURL=handlers.js.map