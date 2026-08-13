/**
 * @vitest-environment jsdom
 * Tests for the depth hop input handlers.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { _test_hooks } from "./handlers.js";
import { createTestBunnyState, createTestFrames, createTestTimers, } from "../testing/fixtures.js";
const { handleHopInput, handleHopRelease } = _test_hooks;
/**
 * Read the animation out of a bunny state.
 *
 * Args:
 *     s: Bunny state to read.
 *
 * Returns:
 *     The current animation state.
 */
function getBunnyAnim(s) {
    return s.animation;
}
describe("handleHopInput", () => {
    let bunnyState;
    let timers;
    let frames;
    beforeEach(() => {
        vi.useFakeTimers();
        bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        frames = createTestFrames();
        timers = createTestTimers(bunnyState, frames, () => false);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("starts turn away transition when called from idle with away direction", () => {
        handleHopInput(bunnyState, timers, "away");
        const anim = getBunnyAnim(bunnyState);
        expect(anim.kind).toBe("transition");
        if (anim.kind === "transition") {
            expect(anim.type).toBe("walk_to_turn_away");
            expect(anim.returnTo).toBe("idle");
            expect(anim.pendingAction).toBe(null);
        }
        expect(timers.idle.isRunning()).toBe(false);
        expect(timers.transition.isRunning()).toBe(true);
    });
    it("starts turn toward transition when called from idle with toward direction", () => {
        handleHopInput(bunnyState, timers, "toward");
        const anim = getBunnyAnim(bunnyState);
        expect(anim.kind).toBe("transition");
        if (anim.kind === "transition") {
            expect(anim.type).toBe("walk_to_turn_toward");
            expect(anim.returnTo).toBe("idle");
        }
    });
    it("starts turn away transition when called from walk", () => {
        bunnyState.animation = { kind: "walk", frameIdx: 0 };
        timers.walk.start();
        handleHopInput(bunnyState, timers, "away");
        const anim = getBunnyAnim(bunnyState);
        expect(anim.kind).toBe("transition");
        if (anim.kind === "transition") {
            expect(anim.type).toBe("walk_to_turn_away");
            expect(anim.returnTo).toBe("walk");
        }
        expect(timers.walk.isRunning()).toBe(false);
        expect(timers.transition.isRunning()).toBe(true);
    });
    it("starts turn toward transition when called from walk", () => {
        bunnyState.animation = { kind: "walk", frameIdx: 0 };
        timers.walk.start();
        handleHopInput(bunnyState, timers, "toward");
        const anim = getBunnyAnim(bunnyState);
        expect(anim.kind).toBe("transition");
        if (anim.kind === "transition") {
            expect(anim.type).toBe("walk_to_turn_toward");
            expect(anim.returnTo).toBe("walk");
        }
    });
    it("sets pendingAction when called during transition", () => {
        bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: "walk", returnTo: "idle" };
        handleHopInput(bunnyState, timers, "away");
        const anim = getBunnyAnim(bunnyState);
        if (anim.kind === "transition") {
            expect(anim.pendingAction).toBe("hop_away");
        }
    });
    it("sets pendingAction to hop_toward when called with toward direction during transition", () => {
        bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: "walk", returnTo: "idle" };
        handleHopInput(bunnyState, timers, "toward");
        const anim = getBunnyAnim(bunnyState);
        if (anim.kind === "transition") {
            expect(anim.pendingAction).toBe("hop_toward");
        }
    });
    it("does nothing when already jumping", () => {
        bunnyState.animation = { kind: "jump", frameIdx: 0 };
        handleHopInput(bunnyState, timers, "away");
        expect(bunnyState.animation.kind).toBe("jump");
    });
    it("does nothing when already hopping", () => {
        bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 0 };
        handleHopInput(bunnyState, timers, "toward");
        const anim = getBunnyAnim(bunnyState);
        expect(anim.kind).toBe("hop");
        if (anim.kind === "hop") {
            expect(anim.direction).toBe("away");
        }
    });
});
describe("handleHopRelease", () => {
    let bunnyState;
    let timers;
    let frames;
    beforeEach(() => {
        vi.useFakeTimers();
        bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        frames = createTestFrames();
        timers = createTestTimers(bunnyState, frames, () => false);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("clears hop pendingAction from idle_to_walk transition", () => {
        bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "hop_away", returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers, () => false);
        const anim = getBunnyAnim(bunnyState);
        expect(anim.kind).toBe("transition");
        if (anim.kind === "transition") {
            expect(anim.type).toBe("idle_to_walk");
            expect(anim.pendingAction).toBe(null);
        }
        expect(timers.transition.isRunning()).toBe(true);
    });
    it("clears hop_toward pendingAction from idle_to_walk same as hop_away", () => {
        bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: "hop_toward", returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers, () => false);
        const anim = getBunnyAnim(bunnyState);
        expect(anim.kind).toBe("transition");
        if (anim.kind === "transition") {
            expect(anim.pendingAction).toBe(null);
        }
    });
    it("cancels walk_to_turn_away transition and returns to walk when horizontal held", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_turn_away", frameIdx: 1, pendingAction: null, returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers, () => true);
        expect(bunnyState.animation.kind).toBe("walk");
        expect(timers.walk.isRunning()).toBe(true);
        expect(timers.transition.isRunning()).toBe(false);
    });
    it("cancels walk_to_turn_away transition and returns to idle when no horizontal held", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_turn_away", frameIdx: 1, pendingAction: null, returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers, () => false);
        expect(bunnyState.animation.kind).toBe("idle");
        expect(timers.idle.isRunning()).toBe(true);
        expect(timers.transition.isRunning()).toBe(false);
    });
    it("cancels walk_to_turn_toward transition and returns to walk when horizontal held", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers, () => true);
        expect(bunnyState.animation.kind).toBe("walk");
        expect(timers.walk.isRunning()).toBe(true);
    });
    it("cancels walk_to_turn_toward transition and returns to idle when no horizontal held", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers, () => false);
        expect(bunnyState.animation.kind).toBe("idle");
        expect(timers.idle.isRunning()).toBe(true);
    });
    it("does nothing for walk_to_idle transition", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: null, returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers, () => false);
        expect(bunnyState.animation.kind).toBe("transition");
        expect(timers.transition.isRunning()).toBe(true);
    });
    it("does nothing for non-transition, non-hop state", () => {
        bunnyState.animation = { kind: "walk", frameIdx: 0 };
        handleHopRelease(bunnyState, timers, () => false);
        expect(bunnyState.animation.kind).toBe("walk");
    });
    it("does nothing for idle state", () => {
        bunnyState.animation = { kind: "idle", frameIdx: 0 };
        handleHopRelease(bunnyState, timers, () => false);
        expect(bunnyState.animation.kind).toBe("idle");
    });
    it("stops hop and returns to walk when horizontal held", () => {
        bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 1 };
        timers.hop.start();
        handleHopRelease(bunnyState, timers, () => true);
        expect(bunnyState.animation.kind).toBe("walk");
        expect(timers.walk.isRunning()).toBe(true);
        expect(timers.hop.isRunning()).toBe(false);
    });
    it("stops hop and returns to idle when no horizontal held", () => {
        bunnyState.animation = { kind: "hop", direction: "toward", frameIdx: 0 };
        timers.hop.start();
        handleHopRelease(bunnyState, timers, () => false);
        expect(bunnyState.animation.kind).toBe("idle");
        expect(timers.idle.isRunning()).toBe(true);
        expect(timers.hop.isRunning()).toBe(false);
    });
    it("does not cancel walk_to_idle transition even with pending hop", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: "hop_away", returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers, () => false);
        expect(bunnyState.animation.kind).toBe("transition");
    });
});
//# sourceMappingURL=handlers.hop.test.js.map