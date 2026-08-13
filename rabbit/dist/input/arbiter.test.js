/**
 * @vitest-environment jsdom
 * Tests for input arbitration.
 *
 * The arbiter is the only writer of effective intent, so these tests assert on
 * `state.intent` and on the real bunny animation it drives.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { _test_hooks } from "./arbiter.js";
import { NEUTRAL_INTENT, createIntent } from "./intent.js";
import { createTestBunnyState, createTestFrames, createTestInputState, createTestTimers, } from "../testing/fixtures.js";
const { resolveIntent, jumpBlocked, createInputArbiter } = _test_hooks;
describe("resolveIntent", () => {
    it("yields to the autopilot when the user asks for nothing", () => {
        expect(resolveIntent(NEUTRAL_INTENT, createIntent("left", null))).toStrictEqual(createIntent("left", null));
    });
    it("prefers the user over the autopilot", () => {
        expect(resolveIntent(createIntent("right", null), createIntent("left", null))).toStrictEqual(createIntent("right", null));
    });
    it("is neutral when neither source wants anything", () => {
        expect(resolveIntent(NEUTRAL_INTENT, NEUTRAL_INTENT)).toStrictEqual(NEUTRAL_INTENT);
    });
    it("counts a vertical-only user intent as a claim on control", () => {
        expect(resolveIntent(createIntent(null, "up"), createIntent("left", null))).toStrictEqual(createIntent(null, "up"));
    });
});
describe("jumpBlocked", () => {
    /**
     * Build arbiter dependencies around a bunny in a given animation.
     *
     * Args:
     *     bunny: Bunny state to wrap.
     *
     * Returns:
     *     Dependencies usable by jumpBlocked.
     */
    function depsFor(bunny) {
        const state = createTestInputState(bunny);
        const frames = createTestFrames();
        return { state, frames, timers: createTestTimers(bunny, frames, () => false) };
    }
    it("allows a jump from idle", () => {
        expect(jumpBlocked(depsFor(createTestBunnyState({ kind: "idle", frameIdx: 0 })))).toBe(false);
    });
    it("allows a jump from a walk", () => {
        expect(jumpBlocked(depsFor(createTestBunnyState({ kind: "walk", frameIdx: 0 })))).toBe(false);
    });
    it("blocks a jump while already jumping", () => {
        expect(jumpBlocked(depsFor(createTestBunnyState({ kind: "jump", frameIdx: 0 })))).toBe(true);
    });
    it("blocks a jump while hopping", () => {
        expect(jumpBlocked(depsFor(createTestBunnyState({ kind: "hop", direction: "away", frameIdx: 0 })))).toBe(true);
    });
    it("blocks a jump that is already pending", () => {
        expect(jumpBlocked(depsFor(createTestBunnyState({
            kind: "transition",
            type: "idle_to_walk",
            frameIdx: 2,
            pendingAction: "jump",
            returnTo: "idle",
        })))).toBe(true);
    });
});
describe("createInputArbiter", () => {
    let bunny;
    let state;
    let frames;
    let timers;
    let arbiter;
    beforeEach(() => {
        vi.useFakeTimers();
        bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        state = createTestInputState(bunny);
        frames = createTestFrames();
        timers = createTestTimers(bunny, frames, () => state.intent.horizontal !== null);
        arbiter = createInputArbiter({ state, frames, timers });
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("starts with both sources neutral", () => {
        expect(arbiter.intentFor("user")).toStrictEqual(NEUTRAL_INTENT);
        expect(arbiter.intentFor("autopilot")).toStrictEqual(NEUTRAL_INTENT);
        expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
    });
    it("applies an autopilot intent when the user is absent", () => {
        arbiter.submit("autopilot", createIntent("left", null));
        expect(state.intent).toStrictEqual(createIntent("left", null));
        expect(bunny.animation.kind).toBe("transition");
    });
    it("overrides the autopilot as soon as the user asks for something", () => {
        arbiter.submit("autopilot", createIntent("left", null));
        arbiter.submit("user", createIntent("right", null));
        expect(state.intent).toStrictEqual(createIntent("right", null));
        expect(bunny.facingRight).toBe(true);
    });
    it("falls back to the autopilot when the user releases", () => {
        arbiter.submit("autopilot", createIntent("left", null));
        arbiter.submit("user", createIntent("right", null));
        arbiter.submit("user", NEUTRAL_INTENT);
        expect(state.intent).toStrictEqual(createIntent("left", null));
    });
    it("goes neutral when both sources release", () => {
        arbiter.submit("user", createIntent("right", null));
        arbiter.submit("user", NEUTRAL_INTENT);
        expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
    });
    it("remembers each source's intent independently", () => {
        arbiter.submit("autopilot", createIntent("left", null));
        arbiter.submit("user", createIntent("right", null));
        expect(arbiter.intentFor("autopilot")).toStrictEqual(createIntent("left", null));
        expect(arbiter.intentFor("user")).toStrictEqual(createIntent("right", null));
    });
    it("does not disturb the animation when the effective intent is unchanged", () => {
        arbiter.submit("user", createIntent("right", null));
        vi.advanceTimersByTime(500);
        const walking = { ...bunny.animation };
        arbiter.submit("user", createIntent("right", null));
        expect(bunny.animation).toStrictEqual(walking);
    });
    it("does not disturb the animation when a losing source changes", () => {
        arbiter.submit("user", createIntent("right", null));
        vi.advanceTimersByTime(500);
        const walking = { ...bunny.animation };
        arbiter.submit("autopilot", createIntent("left", null));
        expect(state.intent).toStrictEqual(createIntent("right", null));
        expect(bunny.animation).toStrictEqual(walking);
    });
    it("lets the user jump", () => {
        arbiter.requestJump("user");
        // Jumping from idle runs the transition first, then a single jump frame.
        expect(bunny.animation.kind).toBe("transition");
        vi.advanceTimersByTime(250);
        expect(bunny.animation.kind).toBe("jump");
    });
    it("lets the autopilot jump while the user is absent", () => {
        bunny.animation = { kind: "walk", frameIdx: 0 };
        arbiter.requestJump("autopilot");
        expect(bunny.animation.kind).toBe("jump");
    });
    it("refuses an autopilot jump while the user holds an intent", () => {
        arbiter.submit("user", createIntent("right", null));
        vi.advanceTimersByTime(500);
        arbiter.requestJump("autopilot");
        expect(bunny.animation.kind).toBe("walk");
    });
    it("refuses a jump while the bunny is already jumping", () => {
        bunny.animation = { kind: "jump", frameIdx: 1 };
        arbiter.requestJump("user");
        expect(bunny.animation).toStrictEqual({ kind: "jump", frameIdx: 1 });
    });
    it("refuses a jump while the bunny is hopping", () => {
        bunny.animation = { kind: "hop", direction: "away", frameIdx: 1 };
        arbiter.requestJump("user");
        expect(bunny.animation).toStrictEqual({ kind: "hop", direction: "away", frameIdx: 1 });
    });
});
//# sourceMappingURL=arbiter.test.js.map