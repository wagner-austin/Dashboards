/**
 * Tests for Bunny entity state machine.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createInitialBunnyState, createBunnyTimers, getBunnyFrame, isHopping, isJumping, isWalking, getHopDirection, } from "./Bunny.js";
function createTestFrames() {
    return {
        walkLeft: ["walkL0", "walkL1", "walkL2"],
        walkRight: ["walkR0", "walkR1", "walkR2"],
        jumpLeft: ["jumpL0", "jumpL1", "jumpL2"],
        jumpRight: ["jumpR0", "jumpR1", "jumpR2"],
        idleLeft: ["idleL0", "idleL1"],
        idleRight: ["idleR0", "idleR1"],
        walkToIdleLeft: ["transL0", "transL1", "transL2"],
        walkToIdleRight: ["transR0", "transR1", "transR2"],
        walkToTurnAwayLeft: ["turnAwayL0", "turnAwayL1"],
        walkToTurnAwayRight: ["turnAwayR0", "turnAwayR1"],
        walkToTurnTowardLeft: ["turnTowardL0", "turnTowardL1"],
        walkToTurnTowardRight: ["turnTowardR0", "turnTowardR1"],
        hopAway: ["hopAway0", "hopAway1", "hopAway2"],
        hopToward: ["hopToward0", "hopToward1", "hopToward2"],
    };
}
function createTestState(animation, facingRight = false) {
    return { facingRight, animation };
}
describe("createInitialBunnyState", () => {
    it("returns idle state facing left", () => {
        const state = createInitialBunnyState();
        expect(state.facingRight).toBe(false);
        expect(state.animation.kind).toBe("idle");
        expect(state.animation.frameIdx).toBe(0);
    });
});
describe("state helper functions", () => {
    it("isHopping returns true when hopping", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0 });
        expect(isHopping(state)).toBe(true);
    });
    it("isHopping returns false when not hopping", () => {
        const state = createTestState({ kind: "idle", frameIdx: 0 });
        expect(isHopping(state)).toBe(false);
    });
    it("isJumping returns true when jumping", () => {
        const state = createTestState({ kind: "jump", frameIdx: 0 });
        expect(isJumping(state)).toBe(true);
    });
    it("isJumping returns false when not jumping", () => {
        const state = createTestState({ kind: "walk", frameIdx: 0 });
        expect(isJumping(state)).toBe(false);
    });
    it("isWalking returns true when walking", () => {
        const state = createTestState({ kind: "walk", frameIdx: 0 });
        expect(isWalking(state)).toBe(true);
    });
    it("isWalking returns false when not walking", () => {
        const state = createTestState({ kind: "idle", frameIdx: 0 });
        expect(isWalking(state)).toBe(false);
    });
    it("getHopDirection returns direction when hopping", () => {
        const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 0 });
        expect(getHopDirection(state)).toBe("toward");
    });
    it("getHopDirection returns null when not hopping", () => {
        const state = createTestState({ kind: "idle", frameIdx: 0 });
        expect(getHopDirection(state)).toBe(null);
    });
});
describe("createBunnyTimers", () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("creates five timers", () => {
        const state = createInitialBunnyState();
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        expect(timers.walk).toBeDefined();
        expect(timers.idle).toBeDefined();
        expect(timers.jump).toBeDefined();
        expect(timers.transition).toBeDefined();
        expect(timers.hop).toBeDefined();
    });
    it("walk timer advances frame index", () => {
        const state = createTestState({ kind: "walk", frameIdx: 0 });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.walk.start();
        expect(state.animation.frameIdx).toBe(0);
        vi.advanceTimersByTime(100);
        expect(state.animation.frameIdx).toBe(1);
        vi.advanceTimersByTime(100);
        expect(state.animation.frameIdx).toBe(2);
        vi.advanceTimersByTime(100);
        expect(state.animation.frameIdx).toBe(0);
    });
    it("walk timer uses right frames when facing right", () => {
        const state = createTestState({ kind: "walk", frameIdx: 0 }, true);
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.walk.start();
        vi.advanceTimersByTime(300);
        expect(state.animation.frameIdx).toBe(0);
    });
    it("walk timer does nothing when not in walk state", () => {
        const state = createTestState({ kind: "idle", frameIdx: 0 });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.walk.start();
        vi.advanceTimersByTime(100);
        expect(state.animation.frameIdx).toBe(0);
    });
    it("idle timer advances frame index", () => {
        const state = createInitialBunnyState();
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.idle.start();
        vi.advanceTimersByTime(200);
        expect(state.animation.frameIdx).toBe(1);
        vi.advanceTimersByTime(200);
        expect(state.animation.frameIdx).toBe(0);
    });
    it("idle timer uses right frames when facing right", () => {
        const state = createTestState({ kind: "idle", frameIdx: 0 }, true);
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.idle.start();
        vi.advanceTimersByTime(200);
        expect(state.animation.frameIdx).toBe(1);
    });
    it("idle timer does nothing when not in idle state", () => {
        const state = createTestState({ kind: "walk", frameIdx: 0 });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.idle.start();
        vi.advanceTimersByTime(200);
        expect(state.animation.frameIdx).toBe(0);
    });
    it("jump timer advances frame and returns to idle when no horizontal held", () => {
        const state = createTestState({ kind: "jump", frameIdx: 0 });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.jump.start();
        vi.advanceTimersByTime(50);
        expect(state.animation.frameIdx).toBe(1);
        vi.advanceTimersByTime(50);
        expect(state.animation.frameIdx).toBe(2);
        vi.advanceTimersByTime(50);
        expect(state.animation.kind).toBe("idle");
        expect(timers.idle.isRunning()).toBe(true);
    });
    it("jump timer returns to walk when horizontal is held", () => {
        const state = createTestState({ kind: "jump", frameIdx: 0 });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => true);
        timers.jump.start();
        vi.advanceTimersByTime(150);
        expect(state.animation.kind).toBe("walk");
        expect(timers.walk.isRunning()).toBe(true);
    });
    it("jump timer uses right frames when facing right and returns to idle", () => {
        const state = createTestState({ kind: "jump", frameIdx: 0 }, true);
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.jump.start();
        vi.advanceTimersByTime(150);
        expect(state.animation.kind).toBe("idle");
    });
    it("jump timer does nothing when not in jump state", () => {
        const state = createTestState({ kind: "walk", frameIdx: 0 });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.jump.start();
        vi.advanceTimersByTime(50);
        expect(state.animation.kind).toBe("walk");
    });
    it("transition timer advances walk_to_idle and switches to idle", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(80);
        expect(state.animation.frameIdx).toBe(1);
        vi.advanceTimersByTime(80);
        expect(state.animation.frameIdx).toBe(2);
        vi.advanceTimersByTime(80);
        expect(state.animation.kind).toBe("idle");
        expect(timers.idle.isRunning()).toBe(true);
    });
    it("transition timer reverses idle_to_walk and switches to walk", () => {
        const state = createTestState({ kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "walk", returnTo: "idle" });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(80);
        expect(state.animation.frameIdx).toBe(1);
        vi.advanceTimersByTime(80);
        expect(state.animation.frameIdx).toBe(0);
        vi.advanceTimersByTime(80);
        expect(state.animation.kind).toBe("walk");
        expect(timers.walk.isRunning()).toBe(true);
    });
    it("transition timer starts jump when pendingAction is jump", () => {
        const state = createTestState({ kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "jump", returnTo: "idle" });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(240);
        expect(state.animation.kind).toBe("jump");
        expect(timers.jump.isRunning()).toBe(true);
    });
    it("transition timer starts walk_to_turn_away when pendingAction is hop_away", () => {
        const state = createTestState({ kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "hop_away", returnTo: "idle" });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(240);
        expect(state.animation.kind).toBe("transition");
        if (state.animation.kind === "transition") {
            expect(state.animation.type).toBe("walk_to_turn_away");
        }
    });
    it("transition timer starts walk_to_turn_toward when pendingAction is hop_toward", () => {
        const state = createTestState({ kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "hop_toward", returnTo: "idle" });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(240);
        expect(state.animation.kind).toBe("transition");
        if (state.animation.kind === "transition") {
            expect(state.animation.type).toBe("walk_to_turn_toward");
        }
    });
    it("transition timer advances walk_to_turn_away and starts hopping", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_away", frameIdx: 0, pendingAction: null, returnTo: "walk" });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(80);
        expect(state.animation.frameIdx).toBe(1);
        vi.advanceTimersByTime(80);
        expect(state.animation.kind).toBe("hop");
        if (state.animation.kind === "hop") {
            expect(state.animation.direction).toBe("away");
        }
        expect(timers.hop.isRunning()).toBe(true);
    });
    it("transition timer advances walk_to_turn_toward and starts hopping", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: "idle" });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(160);
        expect(state.animation.kind).toBe("hop");
        if (state.animation.kind === "hop") {
            expect(state.animation.direction).toBe("toward");
        }
        expect(timers.hop.isRunning()).toBe(true);
    });
    it("transition timer uses right frames for walk_to_turn_away", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_away", frameIdx: 0, pendingAction: null, returnTo: "walk" }, true);
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(160);
        expect(state.animation.kind).toBe("hop");
    });
    it("transition timer uses right frames for walk_to_turn_toward", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: "idle" }, true);
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(160);
        expect(state.animation.kind).toBe("hop");
    });
    it("transition timer uses right frames for walk_to_idle", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" }, true);
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(240);
        expect(state.animation.kind).toBe("idle");
    });
    it("transition timer does nothing when not in transition state", () => {
        const state = createTestState({ kind: "walk", frameIdx: 1 });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.transition.start();
        vi.advanceTimersByTime(80);
        expect(state.animation.kind).toBe("walk");
        expect(state.animation.frameIdx).toBe(1);
    });
    it("hop timer advances frame index for hop_away", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0 });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.hop.start();
        vi.advanceTimersByTime(100);
        expect(state.animation.frameIdx).toBe(1);
        vi.advanceTimersByTime(100);
        expect(state.animation.frameIdx).toBe(2);
        vi.advanceTimersByTime(100);
        expect(state.animation.frameIdx).toBe(0);
    });
    it("hop timer advances frame index for hop_toward", () => {
        const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 0 });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.hop.start();
        vi.advanceTimersByTime(100);
        expect(state.animation.frameIdx).toBe(1);
    });
    it("hop timer does nothing when not in hop state", () => {
        const state = createTestState({ kind: "walk", frameIdx: 0 });
        const frames = createTestFrames();
        const timers = createBunnyTimers(state, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        }, () => false);
        timers.hop.start();
        vi.advanceTimersByTime(100);
        expect(state.animation.frameIdx).toBe(0);
    });
});
describe("getBunnyFrame", () => {
    const frames = createTestFrames();
    it("returns idle frame facing left", () => {
        const state = createTestState({ kind: "idle", frameIdx: 0 });
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["idleL0"]);
        expect(result.frameIdx).toBe(0);
    });
    it("returns idle frame facing right", () => {
        const state = createTestState({ kind: "idle", frameIdx: 1 }, true);
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["idleR1"]);
        expect(result.frameIdx).toBe(1);
    });
    it("wraps idle frame index", () => {
        const state = createTestState({ kind: "idle", frameIdx: 5 });
        const result = getBunnyFrame(state, frames);
        expect(result.frameIdx).toBe(1);
    });
    it("returns walk frame facing left", () => {
        const state = createTestState({ kind: "walk", frameIdx: 1 });
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["walkL1"]);
        expect(result.frameIdx).toBe(1);
    });
    it("returns walk frame facing right", () => {
        const state = createTestState({ kind: "walk", frameIdx: 0 }, true);
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["walkR0"]);
    });
    it("returns empty lines when walk frame index is out of bounds", () => {
        const state = createTestState({ kind: "walk", frameIdx: 999 });
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual([]);
        expect(result.frameIdx).toBe(999);
    });
    it("returns jump frame facing left", () => {
        const state = createTestState({ kind: "jump", frameIdx: 2 });
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["jumpL2"]);
        expect(result.frameIdx).toBe(2);
    });
    it("returns jump frame facing right", () => {
        const state = createTestState({ kind: "jump", frameIdx: 1 }, true);
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["jumpR1"]);
    });
    it("returns empty lines when jump frame index is out of bounds", () => {
        const state = createTestState({ kind: "jump", frameIdx: 999 }, true);
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual([]);
    });
    it("returns hop_away frame", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 1 });
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["hopAway1"]);
        expect(result.frameIdx).toBe(1);
    });
    it("returns hop_toward frame", () => {
        const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 2 });
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["hopToward2"]);
        expect(result.frameIdx).toBe(2);
    });
    it("wraps hop frame index", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 5 });
        const result = getBunnyFrame(state, frames);
        expect(result.frameIdx).toBe(2);
    });
    it("returns idle_to_walk transition frame facing left", () => {
        const state = createTestState({ kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "walk", returnTo: "idle" });
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["transL2"]);
        expect(result.frameIdx).toBe(2);
    });
    it("returns walk_to_idle transition frame facing right", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" }, true);
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["transR0"]);
    });
    it("clamps transition frame index to valid range", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_idle", frameIdx: 100, pendingAction: null, returnTo: "idle" });
        const result = getBunnyFrame(state, frames);
        expect(result.frameIdx).toBe(2);
    });
    it("handles negative transition frame index", () => {
        const state = createTestState({ kind: "transition", type: "idle_to_walk", frameIdx: -5, pendingAction: "walk", returnTo: "idle" });
        const result = getBunnyFrame(state, frames);
        expect(result.frameIdx).toBe(0);
    });
    it("returns walk_to_turn_away frame facing left", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_away", frameIdx: 1, pendingAction: null, returnTo: "walk" });
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["turnAwayL1"]);
    });
    it("returns walk_to_turn_away frame facing right", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_away", frameIdx: 0, pendingAction: null, returnTo: "walk" }, true);
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["turnAwayR0"]);
    });
    it("returns walk_to_turn_toward frame facing left", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: "idle" });
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["turnTowardL0"]);
    });
    it("returns walk_to_turn_toward frame facing right", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_toward", frameIdx: 1, pendingAction: null, returnTo: "idle" }, true);
        const result = getBunnyFrame(state, frames);
        expect(result.lines).toEqual(["turnTowardR1"]);
    });
    it("clamps walk_to_turn_away frame index", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_away", frameIdx: 100, pendingAction: null, returnTo: "walk" });
        const result = getBunnyFrame(state, frames);
        expect(result.frameIdx).toBe(1);
    });
    it("clamps walk_to_turn_toward frame index to min", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_toward", frameIdx: -5, pendingAction: null, returnTo: "idle" });
        const result = getBunnyFrame(state, frames);
        expect(result.frameIdx).toBe(0);
    });
});
//# sourceMappingURL=Bunny.test.js.map