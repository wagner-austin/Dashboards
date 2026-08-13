/**
 * @vitest-environment jsdom
 * Tests for the intent-to-animation reducer.
 *
 * Every case drives the real bunny state machine through real timers; the
 * assertions are on the resulting animation state, not on call counts.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { _test_hooks } from "./reducer.js";
import { NEUTRAL_INTENT, createIntent } from "./intent.js";
import { getHopDirection, } from "../entities/Bunny.js";
import { createTestBunnyState, createTestFrames, createTestInputState, createTestTimers, } from "../testing/fixtures.js";
const { applyVerticalChange, applyHorizontalChange, applyIntentChange } = _test_hooks;
describe("applyIntentChange", () => {
    let bunny;
    let state;
    let frames;
    let timers;
    /**
     * Apply an intent change, honouring the contract that state.intent is
     * written before the reducer runs.
     *
     * Args:
     *     previous: Intent in effect before the change.
     *     next: Intent now in effect.
     */
    function apply(previous, next) {
        state.intent = next;
        applyIntentChange(previous, next, state, frames, timers);
    }
    /**
     * Replace the bunny's animation for a test starting mid-state.
     *
     * Args:
     *     animation: Animation to install.
     */
    function setAnimation(animation) {
        bunny.animation = animation;
    }
    beforeEach(() => {
        vi.useFakeTimers();
        bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        state = createTestInputState(bunny);
        frames = createTestFrames();
        timers = createTestTimers(bunny, frames, () => state.intent.horizontal !== null);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    describe("horizontal intent on the ground", () => {
        it("starts a transition toward walking left", () => {
            apply(NEUTRAL_INTENT, createIntent("left", null));
            expect(bunny.animation.kind).toBe("transition");
            expect(bunny.facingRight).toBe(false);
        });
        it("starts a transition toward walking right and faces right", () => {
            apply(NEUTRAL_INTENT, createIntent("right", null));
            expect(bunny.animation.kind).toBe("transition");
            expect(bunny.facingRight).toBe(true);
        });
        it("reaches a walk once the transition completes", () => {
            apply(NEUTRAL_INTENT, createIntent("right", null));
            vi.advanceTimersByTime(500);
            expect(bunny.animation.kind).toBe("walk");
        });
        it("switches direction while already walking", () => {
            setAnimation({ kind: "walk", frameIdx: 1 });
            apply(createIntent("right", null), createIntent("left", null));
            expect(bunny.animation.kind).toBe("walk");
            expect(bunny.facingRight).toBe(false);
        });
        it("returns to idle when horizontal intent is released", () => {
            setAnimation({ kind: "walk", frameIdx: 1 });
            apply(createIntent("right", null), NEUTRAL_INTENT);
            vi.advanceTimersByTime(500);
            expect(bunny.animation.kind).toBe("idle");
        });
        it("does nothing when the horizontal intent is unchanged", () => {
            setAnimation({ kind: "walk", frameIdx: 2 });
            apply(createIntent("right", null), createIntent("right", null));
            expect(bunny.animation).toStrictEqual({ kind: "walk", frameIdx: 2 });
        });
        it("does nothing when both intents are neutral", () => {
            apply(NEUTRAL_INTENT, NEUTRAL_INTENT);
            expect(bunny.animation).toStrictEqual({ kind: "idle", frameIdx: 0 });
        });
    });
    describe("horizontal intent while airborne", () => {
        it("only turns the bunny while jumping", () => {
            setAnimation({ kind: "jump", frameIdx: 0 });
            apply(NEUTRAL_INTENT, createIntent("right", null));
            expect(bunny.animation.kind).toBe("jump");
            expect(bunny.facingRight).toBe(true);
        });
        it("turns the bunny left while jumping", () => {
            setAnimation({ kind: "jump", frameIdx: 0 });
            bunny.facingRight = true;
            apply(NEUTRAL_INTENT, createIntent("left", null));
            expect(bunny.facingRight).toBe(false);
        });
        it("leaves facing untouched when airborne with no horizontal intent", () => {
            setAnimation({ kind: "jump", frameIdx: 0 });
            bunny.facingRight = true;
            apply(createIntent("right", null), NEUTRAL_INTENT);
            expect(bunny.facingRight).toBe(true);
            expect(bunny.animation.kind).toBe("jump");
        });
        it("only turns the bunny while hopping", () => {
            setAnimation({ kind: "hop", direction: "away", frameIdx: 0 });
            apply(createIntent(null, "up"), createIntent("right", "up"));
            expect(bunny.animation.kind).toBe("hop");
            expect(bunny.facingRight).toBe(true);
        });
        it("treats a vertical intent as airborne even before the hop starts", () => {
            apply(NEUTRAL_INTENT, createIntent("right", "up"));
            expect(bunny.facingRight).toBe(true);
            expect(bunny.animation.kind).toBe("transition");
        });
    });
    describe("vertical intent", () => {
        it("begins turning away when up is requested", () => {
            apply(NEUTRAL_INTENT, createIntent(null, "up"));
            expect(bunny.animation).toStrictEqual({
                kind: "transition",
                type: "walk_to_turn_away",
                frameIdx: 0,
                pendingAction: null,
                returnTo: "idle",
            });
        });
        it("begins turning toward when down is requested", () => {
            apply(NEUTRAL_INTENT, createIntent(null, "down"));
            expect(bunny.animation).toStrictEqual({
                kind: "transition",
                type: "walk_to_turn_toward",
                frameIdx: 0,
                pendingAction: null,
                returnTo: "idle",
            });
        });
        it("reaches a hop once the turn completes", () => {
            apply(NEUTRAL_INTENT, createIntent(null, "up"));
            vi.advanceTimersByTime(500);
            expect(bunny.animation.kind).toBe("hop");
            expect(getHopDirection(bunny)).toBe("away");
        });
        it("returns to idle when vertical intent is released", () => {
            setAnimation({ kind: "hop", direction: "away", frameIdx: 0 });
            apply(createIntent(null, "up"), NEUTRAL_INTENT);
            expect(bunny.animation).toStrictEqual({ kind: "idle", frameIdx: 0 });
        });
        it("resumes walking when vertical is released with horizontal held", () => {
            setAnimation({ kind: "hop", direction: "away", frameIdx: 0 });
            apply(createIntent("right", "up"), createIntent("right", null));
            expect(bunny.animation.kind).toBe("walk");
        });
        it("switches from hopping away to hopping toward", () => {
            setAnimation({ kind: "hop", direction: "away", frameIdx: 0 });
            apply(createIntent(null, "up"), createIntent(null, "down"));
            vi.advanceTimersByTime(500);
            expect(bunny.animation.kind).toBe("hop");
            expect(getHopDirection(bunny)).toBe("toward");
        });
        it("switches from hopping toward to hopping away", () => {
            setAnimation({ kind: "hop", direction: "toward", frameIdx: 0 });
            apply(createIntent(null, "down"), createIntent(null, "up"));
            vi.advanceTimersByTime(500);
            expect(bunny.animation.kind).toBe("hop");
            expect(getHopDirection(bunny)).toBe("away");
        });
        it("does nothing when the vertical intent is unchanged", () => {
            setAnimation({ kind: "hop", direction: "away", frameIdx: 1 });
            applyVerticalChange(createIntent(null, "up"), createIntent(null, "up"), state, timers);
            expect(bunny.animation).toStrictEqual({ kind: "hop", direction: "away", frameIdx: 1 });
        });
    });
    describe("applyHorizontalChange in isolation", () => {
        it("can be driven without the vertical pass", () => {
            applyHorizontalChange(NEUTRAL_INTENT, createIntent("left", null), state, frames, timers);
            expect(bunny.animation.kind).toBe("transition");
        });
    });
});
//# sourceMappingURL=reducer.test.js.map