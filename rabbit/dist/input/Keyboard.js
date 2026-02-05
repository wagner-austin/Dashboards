/**
 * Keyboard input handling.
 */
export function setupKeyboardControls(state, bunnyFrames, bunnyTimers, treeSizes) {
    document.addEventListener("keydown", (e) => {
        if (e.repeat)
            return;
        const key = e.key.toLowerCase();
        const isLeftKey = e.key === "ArrowLeft" || key === "a";
        const isRightKey = e.key === "ArrowRight" || key === "d";
        if (isLeftKey) {
            handleWalkInput(state.bunny, bunnyFrames, bunnyTimers, false);
        }
        else if (isRightKey) {
            handleWalkInput(state.bunny, bunnyFrames, bunnyTimers, true);
        }
        else if (e.key === " " && !state.bunny.isJumping && !state.bunny.pendingJump) {
            handleJumpInput(state.bunny, bunnyFrames, bunnyTimers);
            e.preventDefault();
        }
        else if (key === "r") {
            state.tree.centerX = state.viewport.width + 60;
            state.groundScrollX = 0;
        }
        else if (key === "w" || e.key === "ArrowUp") {
            if (state.tree.targetSizeIdx < treeSizes.length - 1) {
                state.tree.targetSizeIdx++;
            }
        }
        else if (key === "s" || e.key === "ArrowDown") {
            if (state.tree.targetSizeIdx > 0) {
                state.tree.targetSizeIdx--;
            }
        }
    });
}
function handleJumpInput(bunny, frames, timers) {
    // Store pre-jump animation state
    const wasIdle = bunny.currentAnimation === "idle";
    const wasWalking = bunny.currentAnimation === "walk";
    if (wasIdle) {
        // From idle: play crouch transition first, then jump
        bunny.preJumpAnimation = "idle";
        bunny.pendingJump = true;
        timers.idle.stop();
        const transitionFrames = bunny.facingRight ? frames.walkToIdleRight : frames.walkToIdleLeft;
        bunny.currentAnimation = "idle_to_walk";
        bunny.bunnyFrameIdx = transitionFrames.length - 1;
        timers.transition.start();
    }
    else if (wasWalking) {
        // From walk: jump immediately
        bunny.preJumpAnimation = "walk";
        bunny.isJumping = true;
        bunny.jumpFrameIdx = 0;
        timers.walk.stop();
        timers.jump.start();
    }
    else {
        // From transition: jump immediately
        bunny.preJumpAnimation = bunny.isWalking ? "walk" : "idle";
        bunny.isJumping = true;
        bunny.jumpFrameIdx = 0;
        timers.transition.stop();
        timers.jump.start();
    }
}
function handleWalkInput(bunny, frames, timers, goingRight) {
    const sameDirection = bunny.facingRight === goingRight;
    if (bunny.isWalking && sameDirection && bunny.currentAnimation === "walk") {
        // Already walking this direction, stop with transition
        bunny.isWalking = false;
        timers.walk.stop();
        bunny.currentAnimation = "walk_to_idle";
        bunny.bunnyFrameIdx = 0;
        timers.transition.start();
    }
    else {
        // Start walking (or switch direction, or interrupt transition)
        const wasIdle = bunny.currentAnimation === "idle";
        const wasInTransition = bunny.currentAnimation === "walk_to_idle" || bunny.currentAnimation === "idle_to_walk";
        bunny.facingRight = goingRight;
        bunny.isWalking = true;
        if (wasIdle) {
            // Start reverse transition: idle → walk
            timers.idle.stop();
            const transitionFrames = goingRight ? frames.walkToIdleRight : frames.walkToIdleLeft;
            bunny.currentAnimation = "idle_to_walk";
            bunny.bunnyFrameIdx = transitionFrames.length - 1;
            timers.transition.start();
        }
        else {
            // Switching direction or interrupting transition - go directly to walk
            if (wasInTransition) {
                timers.transition.stop();
            }
            bunny.currentAnimation = "walk";
            bunny.bunnyFrameIdx = 0;
            timers.walk.start();
        }
    }
}
//# sourceMappingURL=Keyboard.js.map