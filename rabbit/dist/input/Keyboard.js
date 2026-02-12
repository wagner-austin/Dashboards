/**
 * Keyboard input handling with unified input model.
 *
 * Uses raw input tracking (horizontalHeld, verticalHeld) that both keyboard
 * and touch inputs set. Movement processing interprets these based on bunny
 * animation state, ensuring consistent behavior across input methods.
 */
import { isHopping, isJumping, } from "../entities/Bunny.js";
import { DEFAULT_CAMERA_Z, wrapDepth } from "../world/Projection.js";
import { isPendingJump, handleJumpInput, handleWalkKeyDown, handleWalkKeyUp, handleHopInput, handleHopRelease, } from "./handlers.js";
/**
 * Process input state change and trigger appropriate animations.
 *
 * Called when raw input changes (key press/release or touch direction change).
 * Compares previous and new input to determine which handlers to call.
 * This is the single source of truth for input-to-animation mapping.
 *
 * Args:
 *     prevHorizontal: Previous horizontal input.
 *     prevVertical: Previous vertical input.
 *     newHorizontal: New horizontal input.
 *     newVertical: New vertical input.
 *     state: Input state containing bunny.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 */
export function processInputChange(prevHorizontal, prevVertical, newHorizontal, newVertical, state, bunnyFrames, bunnyTimers) {
    // Callback to check current horizontal input for animation completion
    const isHorizontalHeld = () => state.horizontalHeld !== null;
    // Handle vertical (hop) changes first
    const wasVertical = prevVertical !== null;
    const isVertical = newVertical !== null;
    if (!wasVertical && isVertical) {
        // Started vertical movement - begin hop
        const direction = newVertical === "up" ? "away" : "toward";
        handleHopInput(state.bunny, bunnyTimers, direction);
    }
    else if (wasVertical && !isVertical) {
        // Ended vertical movement - stop hop
        handleHopRelease(state.bunny, bunnyTimers, isHorizontalHeld);
    }
    else if (prevVertical === "up" && newVertical === "down") {
        // Switched from up to down
        handleHopRelease(state.bunny, bunnyTimers, isHorizontalHeld);
        handleHopInput(state.bunny, bunnyTimers, "toward");
    }
    else if (prevVertical === "down" && newVertical === "up") {
        // Switched from down to up
        handleHopRelease(state.bunny, bunnyTimers, isHorizontalHeld);
        handleHopInput(state.bunny, bunnyTimers, "away");
    }
    // Handle horizontal changes
    const inAir = isHopping(state.bunny) || isJumping(state.bunny) || newVertical !== null;
    if (inAir) {
        // While in air: update facing direction so bunny faces correct way when landing
        if (newHorizontal === "left") {
            state.bunny.facingRight = false;
        }
        else if (newHorizontal === "right") {
            state.bunny.facingRight = true;
        }
    }
    else {
        // Not in air: horizontal controls walk
        if (newHorizontal === "left" && prevHorizontal !== "left") {
            handleWalkKeyDown(state.bunny, bunnyFrames, bunnyTimers, false);
        }
        else if (newHorizontal === "right" && prevHorizontal !== "right") {
            handleWalkKeyDown(state.bunny, bunnyFrames, bunnyTimers, true);
        }
        else if (newHorizontal === null && prevHorizontal !== null) {
            handleWalkKeyUp(state.bunny, bunnyTimers);
        }
    }
}
/**
 * Setup keyboard controls for the game.
 *
 * Attaches keydown and keyup listeners that update raw input state
 * and call processInputChange for animation handling.
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
        const isUpKey = e.key === "ArrowUp" || key === "w";
        const isDownKey = e.key === "ArrowDown" || key === "s";
        const prevHorizontal = state.horizontalHeld;
        const prevVertical = state.verticalHeld;
        if (isLeftKey) {
            state.horizontalHeld = "left";
        }
        else if (isRightKey) {
            state.horizontalHeld = "right";
        }
        else if (isUpKey) {
            state.verticalHeld = "up";
        }
        else if (isDownKey) {
            state.verticalHeld = "down";
        }
        else if (e.key === " " && !isJumping(state.bunny) && !isPendingJump(state.bunny)) {
            handleJumpInput(state.bunny, bunnyFrames, bunnyTimers);
            e.preventDefault();
            return;
        }
        else if (key === "r") {
            state.camera = { x: 0, z: DEFAULT_CAMERA_Z };
            return;
        }
        else {
            return;
        }
        processInputChange(prevHorizontal, prevVertical, state.horizontalHeld, state.verticalHeld, state, bunnyFrames, bunnyTimers);
    });
    document.addEventListener("keyup", (e) => {
        const key = e.key.toLowerCase();
        const isLeftKey = e.key === "ArrowLeft" || key === "a";
        const isRightKey = e.key === "ArrowRight" || key === "d";
        const isUpKey = e.key === "ArrowUp" || key === "w";
        const isDownKey = e.key === "ArrowDown" || key === "s";
        const prevHorizontal = state.horizontalHeld;
        const prevVertical = state.verticalHeld;
        if (isLeftKey && state.horizontalHeld === "left") {
            state.horizontalHeld = null;
        }
        else if (isRightKey && state.horizontalHeld === "right") {
            state.horizontalHeld = null;
        }
        else if (isUpKey && state.verticalHeld === "up") {
            state.verticalHeld = null;
        }
        else if (isDownKey && state.verticalHeld === "down") {
            state.verticalHeld = null;
        }
        else {
            return;
        }
        processInputChange(prevHorizontal, prevVertical, state.horizontalHeld, state.verticalHeld, state, bunnyFrames, bunnyTimers);
    });
}
/** Camera Z movement speed per frame. */
const CAMERA_Z_SPEED = 0.5;
/**
 * Process camera depth movement based on hop state.
 *
 * Camera moves when bunny is hopping, with infinite wrapping at depth bounds.
 * Moving "toward" decreases Z (toward viewer).
 * Moving "away" increases Z (into scene).
 *
 * Args:
 *     state: Input state with bunny, camera, and depthBounds.
 */
export function processDepthMovement(state) {
    const anim = state.bunny.animation;
    if (anim.kind !== "hop") {
        return;
    }
    const delta = anim.direction === "toward" ? -CAMERA_Z_SPEED : CAMERA_Z_SPEED;
    const newZ = wrapDepth(state.camera.z + delta, state.depthBounds.minZ, state.depthBounds.maxZ);
    state.camera = { ...state.camera, z: newZ };
}
/** Camera X movement speed per frame */
const CAMERA_X_SPEED = 2;
/**
 * Process horizontal camera movement.
 *
 * Camera moves horizontally when bunny is hopping or walking and
 * horizontal input is held. Uses same speed for both modes.
 *
 * Args:
 *     state: Input state with bunny, camera, and horizontalHeld.
 */
export function processHorizontalMovement(state) {
    const anim = state.bunny.animation;
    const isMoving = anim.kind === "hop" || anim.kind === "walk" || anim.kind === "jump";
    if (!isMoving || state.horizontalHeld === null) {
        return;
    }
    const direction = state.horizontalHeld === "left" ? -1 : 1;
    state.camera = { ...state.camera, x: state.camera.x + CAMERA_X_SPEED * direction };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    handleJumpInput,
    handleWalkKeyDown,
    handleWalkKeyUp,
    handleHopInput,
    handleHopRelease,
    isPendingJump,
    processInputChange,
    processDepthMovement,
    processHorizontalMovement,
    CAMERA_Z_SPEED,
    CAMERA_X_SPEED,
};
//# sourceMappingURL=Keyboard.js.map