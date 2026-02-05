/**
 * Bunny entity - state, animations, and frame selection.
 */
import { createAnimationTimer } from "../loaders/sprites.js";
export function createInitialBunnyState() {
    return {
        facingRight: false,
        currentAnimation: "idle",
        bunnyFrameIdx: 0,
        isJumping: false,
        jumpFrameIdx: 0,
        isWalking: false,
        pendingJump: false,
        preJumpAnimation: null,
    };
}
export function createBunnyTimers(state, frames, intervals) {
    const walkTimer = createAnimationTimer(intervals.walk, () => {
        if (!state.isJumping && state.currentAnimation === "walk") {
            const walkFrames = state.facingRight ? frames.walkRight : frames.walkLeft;
            state.bunnyFrameIdx = (state.bunnyFrameIdx + 1) % walkFrames.length;
        }
    });
    const idleTimer = createAnimationTimer(intervals.idle, () => {
        if (!state.isJumping && state.currentAnimation === "idle") {
            const idleFrames = state.facingRight ? frames.idleRight : frames.idleLeft;
            state.bunnyFrameIdx = (state.bunnyFrameIdx + 1) % idleFrames.length;
        }
    });
    const jumpTimer = createAnimationTimer(intervals.jump, () => {
        const jumpFrames = state.facingRight ? frames.jumpRight : frames.jumpLeft;
        state.jumpFrameIdx++;
        if (state.jumpFrameIdx >= jumpFrames.length) {
            state.isJumping = false;
            state.jumpFrameIdx = 0;
            jumpTimer.stop();
            // After jump, transition back based on pre-jump state
            if (state.preJumpAnimation === "idle") {
                // Was idle before jump, play landing transition
                state.currentAnimation = "walk_to_idle";
                state.bunnyFrameIdx = 0;
                transitionTimer.start();
            }
            else if (state.preJumpAnimation === "walk") {
                // Was walking before jump, resume walk
                state.currentAnimation = "walk";
                state.bunnyFrameIdx = 0;
                walkTimer.start();
            }
            state.preJumpAnimation = null;
        }
    });
    const transitionTimer = createAnimationTimer(intervals.transition, () => {
        if (state.isJumping)
            return;
        const transitionFrames = state.facingRight
            ? frames.walkToIdleRight
            : frames.walkToIdleLeft;
        if (state.currentAnimation === "walk_to_idle") {
            state.bunnyFrameIdx++;
            if (state.bunnyFrameIdx >= transitionFrames.length) {
                state.currentAnimation = "idle";
                state.bunnyFrameIdx = 0;
                transitionTimer.stop();
                idleTimer.start();
            }
        }
        else if (state.currentAnimation === "idle_to_walk") {
            state.bunnyFrameIdx--;
            if (state.bunnyFrameIdx < 0) {
                transitionTimer.stop();
                // Check if we have a pending jump
                if (state.pendingJump) {
                    state.pendingJump = false;
                    state.isJumping = true;
                    state.jumpFrameIdx = 0;
                    jumpTimer.start();
                }
                else {
                    state.currentAnimation = "walk";
                    state.bunnyFrameIdx = 0;
                    walkTimer.start();
                }
            }
        }
    });
    return { walk: walkTimer, idle: idleTimer, jump: jumpTimer, transition: transitionTimer };
}
export function getBunnyFrame(state, frames) {
    let bunnyFrames;
    let frameIdx;
    if (state.isJumping) {
        bunnyFrames = state.facingRight ? frames.jumpRight : frames.jumpLeft;
        frameIdx = state.jumpFrameIdx;
    }
    else if (state.currentAnimation === "idle") {
        bunnyFrames = state.facingRight ? frames.idleRight : frames.idleLeft;
        frameIdx = state.bunnyFrameIdx % bunnyFrames.length;
    }
    else if (state.currentAnimation === "walk_to_idle" || state.currentAnimation === "idle_to_walk") {
        bunnyFrames = state.facingRight ? frames.walkToIdleRight : frames.walkToIdleLeft;
        frameIdx = Math.max(0, Math.min(state.bunnyFrameIdx, bunnyFrames.length - 1));
    }
    else {
        bunnyFrames = state.facingRight ? frames.walkRight : frames.walkLeft;
        frameIdx = state.bunnyFrameIdx;
    }
    const frame = bunnyFrames[frameIdx];
    const lines = frame !== undefined ? frame.split("\n") : [];
    return { lines, frameIdx };
}
//# sourceMappingURL=Bunny.js.map