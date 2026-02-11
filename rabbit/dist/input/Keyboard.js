/**
 * Keyboard input handling.
 */
import { isHopping, isJumping, } from "../entities/Bunny.js";
import { DEFAULT_CAMERA_Z } from "../world/Projection.js";
/**
 * Setup keyboard controls for the game.
 *
 * Args:
 *     state: Mutable input state.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 */
export function setupKeyboardControls(state, bunnyFrames, bunnyTimers) {
    document.addEventListener("keydown", (e) => {
        if (e.repeat) {
            return;
        }
        const key = e.key.toLowerCase();
        const isLeftKey = e.key === "ArrowLeft" || key === "a";
        const isRightKey = e.key === "ArrowRight" || key === "d";
        if (isLeftKey) {
            if (isHopping(state.bunny)) {
                state.slideKeyHeld = "left";
            }
            else {
                handleWalkInput(state.bunny, bunnyFrames, bunnyTimers, false);
            }
        }
        else if (isRightKey) {
            if (isHopping(state.bunny)) {
                state.slideKeyHeld = "right";
            }
            else {
                handleWalkInput(state.bunny, bunnyFrames, bunnyTimers, true);
            }
        }
        else if (e.key === " " && !isJumping(state.bunny) && !isPendingJump(state.bunny)) {
            handleJumpInput(state.bunny, bunnyFrames, bunnyTimers);
            e.preventDefault();
        }
        else if (key === "r") {
            state.camera = { x: 0, z: DEFAULT_CAMERA_Z };
        }
        else if (key === "w" || e.key === "ArrowUp") {
            state.hopKeyHeld = "away";
            handleHopInput(state.bunny, bunnyTimers, "away");
        }
        else if (key === "s" || e.key === "ArrowDown") {
            state.hopKeyHeld = "toward";
            handleHopInput(state.bunny, bunnyTimers, "toward");
        }
    });
    document.addEventListener("keyup", (e) => {
        const key = e.key.toLowerCase();
        switch (true) {
            case key === "w":
            case e.key === "ArrowUp":
            case key === "s":
            case e.key === "ArrowDown":
                state.hopKeyHeld = null;
                state.slideKeyHeld = null;
                handleHopRelease(state.bunny, bunnyTimers);
                break;
            case key === "a":
            case e.key === "ArrowLeft":
                if (state.slideKeyHeld === "left") {
                    state.slideKeyHeld = null;
                }
                break;
            case key === "d":
            case e.key === "ArrowRight":
                if (state.slideKeyHeld === "right") {
                    state.slideKeyHeld = null;
                }
                break;
        }
    });
}
/** Camera Z movement speed per frame */
const CAMERA_Z_SPEED = 0.5;
/** Minimum camera Z (closest to scene) */
const MIN_CAMERA_Z = -500;
/** Maximum camera Z (farthest from scene) */
const MAX_CAMERA_Z = 500;
/**
 * Process camera depth movement based on hop state.
 *
 * Camera only moves when bunny is actually hopping, not during transitions.
 *
 * Args:
 *     state: Input state with bunny and camera.
 */
export function processDepthMovement(state) {
    const anim = state.bunny.animation;
    if (anim.kind !== "hop") {
        return;
    }
    let newZ = state.camera.z;
    if (anim.direction === "toward") {
        newZ = Math.max(state.camera.z - CAMERA_Z_SPEED, MIN_CAMERA_Z);
    }
    else {
        newZ = Math.min(state.camera.z + CAMERA_Z_SPEED, MAX_CAMERA_Z);
    }
    state.camera = { ...state.camera, z: newZ };
}
/** Camera X movement speed per frame when sliding during hop */
const CAMERA_X_SPEED = 2;
/**
 * Process horizontal camera movement when sliding during hop.
 *
 * Camera only moves horizontally when bunny is hopping and A/D is held.
 *
 * Args:
 *     state: Input state with bunny, camera, and slideKeyHeld.
 */
export function processHorizontalMovement(state) {
    if (state.bunny.animation.kind !== "hop" || state.slideKeyHeld === null) {
        return;
    }
    const direction = state.slideKeyHeld === "left" ? -1 : 1;
    state.camera = { ...state.camera, x: state.camera.x + CAMERA_X_SPEED * direction };
}
/**
 * Check if bunny has a pending jump.
 *
 * Args:
 *     bunny: Bunny state.
 *
 * Returns:
 *     True if in transition with pending jump action.
 */
function isPendingJump(bunny) {
    return bunny.animation.kind === "transition" && bunny.animation.pendingAction === "jump";
}
/**
 * Handle jump input.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 */
function handleJumpInput(bunny, frames, timers) {
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
        bunny.animation = { kind: "jump", frameIdx: 0, returnTo: "walk" };
        timers.jump.start();
    }
    else if (anim.kind === "transition") {
        timers.transition.stop();
        const returnTo = anim.returnTo === "walk" ? "walk" : "idle";
        bunny.animation = { kind: "jump", frameIdx: 0, returnTo };
        timers.jump.start();
    }
}
/**
 * Handle walk input.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     frames: Bunny animation frames.
 *     timers: Bunny animation timers.
 *     goingRight: Direction of movement.
 */
function handleWalkInput(bunny, frames, timers, goingRight) {
    const anim = bunny.animation;
    const sameDirection = bunny.facingRight === goingRight;
    if (anim.kind === "walk" && sameDirection) {
        timers.walk.stop();
        bunny.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" };
        timers.transition.start();
    }
    else if (anim.kind === "idle") {
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
        bunny.facingRight = goingRight;
        bunny.animation.frameIdx = 0;
    }
}
/**
 * Handle hop input (W/S key pressed).
 *
 * Starts the animation sequence for hopping into depth (away) or out (toward).
 * From idle: idle → walk_to_turn → hop (loop)
 * From walk: walk → walk_to_turn → hop (loop)
 *
 * Args:
 *     bunny: Bunny state to update.
 *     timers: Bunny animation timers.
 *     direction: "away" for W key, "toward" for S key.
 */
function handleHopInput(bunny, timers, direction) {
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
 * Handle hop release (W/S key released).
 *
 * Stops the hopping animation and transitions back to previous state.
 * If released during transition, cancels and returns to previous state.
 *
 * Args:
 *     bunny: Bunny state to update.
 *     timers: Bunny animation timers.
 */
function handleHopRelease(bunny, timers) {
    const anim = bunny.animation;
    // If in transition, check if it's a hop-related transition
    if (anim.kind === "transition") {
        // Cancel turn transitions (they're specifically for hopping)
        if (anim.type === "walk_to_turn_away" || anim.type === "walk_to_turn_toward") {
            timers.transition.stop();
            if (anim.returnTo === "idle") {
                bunny.animation = { kind: "idle", frameIdx: 0 };
                timers.idle.start();
            }
            else {
                bunny.animation = { kind: "walk", frameIdx: 0 };
                timers.walk.start();
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
    const returnTo = anim.returnTo;
    if (returnTo === "walk") {
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
    handleJumpInput,
    handleWalkInput,
    handleHopInput,
    handleHopRelease,
    processDepthMovement,
    processHorizontalMovement,
    isPendingJump,
    CAMERA_Z_SPEED,
    MIN_CAMERA_Z,
    MAX_CAMERA_Z,
    CAMERA_X_SPEED,
};
//# sourceMappingURL=Keyboard.js.map