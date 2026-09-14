export function createCompanion() {
    return { x: 115, z: 12, facingRight: false, mode: "idle", clock: 0,
        jumpTime: 0, wasLeaderJumping: false };
}
/** Speed is bounded and stopping never overshoots, even after a long frame. */
export function stepCompanion(state, input) {
    const dt = Math.max(0, Math.min(input.deltaTime, 0.1));
    let x = state.x - input.cameraDx;
    let z = state.z - input.cameraDz;
    let facingRight = state.facingRight;
    const targetX = input.facingRight ? -115 : 115;
    const dx = targetX - x;
    const dz = 12 - z;
    const distance = Math.hypot(dx, dz);
    // Separate enter/leave distances prevent flicker between walking and running.
    const running = distance > 65 || (state.mode === "run" && distance > 25);
    const speed = running ? 210 : 100;
    const travel = Math.min(distance, speed * dt);
    if (distance > 3) {
        x += dx / distance * travel;
        z += dz / distance * travel;
        if (Math.abs(dx) > 2)
            facingRight = dx > 0;
    }
    const startsJump = input.jumping && !state.wasLeaderJumping && state.jumpTime <= 0;
    const jumpTime = Math.max(0, (startsJump ? 0.6 : state.jumpTime) - dt);
    const requested = jumpTime > 0 ? "jump" : distance <= 3 ? "idle"
        : Math.abs(dz) > Math.abs(dx) * 0.6 ? (dz > 0 ? "hopAway" : "hopToward")
            : running ? "run" : "walk";
    const mode = transitionMode(state, requested);
    return { x, z, facingRight, jumpTime, mode,
        clock: mode === state.mode ? state.clock + dt : 0,
        wasLeaderJumping: input.jumping };
}
/** Fixed frame canvases preserve the jump's actual vertical motion. */
export function companionFrame(state, frames, sprint) {
    const sequence = selectSequence(state, frames, sprint);
    const interval = state.mode === "idle" ? 0.45 : state.mode === "jump" ? 0.6 / sequence.length
        : state.mode === "run" ? 0.075 : 0.12;
    const index = state.mode === "jump" || state.mode === "settle" || state.mode === "turnAway" || state.mode === "turnToward"
        ? Math.min(sequence.length - 1, Math.floor(state.clock / interval))
        : Math.floor(state.clock / interval) % sequence.length;
    const frame = sequence[index];
    if (frame === undefined)
        throw new Error("RABBIT_COMPANION_FRAME: Animation has no frame at the requested index.");
    return frame.split("\n");
}
function transitionMode(state, requested) {
    if (requested === "jump")
        return requested;
    if ((state.mode === "turnAway" || state.mode === "turnToward" || state.mode === "settle") && state.clock < 0.24)
        return state.mode;
    if (requested === "hopAway" && state.mode !== "hopAway" && state.mode !== "turnAway")
        return "turnAway";
    if (requested === "hopToward" && state.mode !== "hopToward" && state.mode !== "turnToward")
        return "turnToward";
    if (requested === "idle" && (state.mode === "walk" || state.mode === "run"))
        return "settle";
    return requested;
}
function selectSequence(state, frames, sprint) {
    const right = state.facingRight;
    switch (state.mode) {
        case "idle": return right ? frames.idleRight : frames.idleLeft;
        case "walk": return right ? frames.walkRight : frames.walkLeft;
        case "run": return right ? sprint.right : sprint.left;
        case "jump": return right ? frames.jumpRight : frames.jumpLeft;
        case "settle": return right ? frames.walkToIdleRight : frames.walkToIdleLeft;
        case "turnAway": return right ? frames.walkToTurnAwayRight : frames.walkToTurnAwayLeft;
        case "turnToward": return right ? frames.walkToTurnTowardRight : frames.walkToTurnTowardLeft;
        case "hopAway": return frames.hopAway;
        case "hopToward": return frames.hopToward;
    }
}
export const _test_hooks = { createCompanion, stepCompanion, companionFrame, transitionMode, selectSequence };
//# sourceMappingURL=Companion.js.map