/**
 * @vitest-environment jsdom
 * Tests for the autopilot controller.
 *
 * These run the real arbiter, the real activity tracker, and the real bunny
 * state machine, so what is asserted is the animation the autopilot actually
 * produces rather than the calls it makes.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { _test_hooks } from "./controller.js";
import { createInputArbiter } from "./arbiter.js";
import { createActivityTracker } from "./activity.js";
import { NEUTRAL_INTENT, createIntent } from "./intent.js";
import { createSequenceRandom, createTestBunnyState, createTestFrames, createTestInputState, createTestTimers, } from "../testing/fixtures.js";
const { createAutopilotController } = _test_hooks;
/** Engages after one second of idle; always walks, never hops. */
const WALK_ONLY = {
    enabled: true,
    idleDelay: 1,
    minLeg: 4,
    maxLeg: 4,
    minPause: 2,
    maxPause: 2,
    turnChance: 0,
    hopChance: 0,
    jumpChance: 0,
};
describe("createAutopilotController", () => {
    let bunny;
    let state;
    let frames;
    let timers;
    let arbiter;
    let activity;
    beforeEach(() => {
        vi.useFakeTimers();
        bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        state = createTestInputState(bunny);
        frames = createTestFrames();
        timers = createTestTimers(bunny, frames, () => state.intent.horizontal !== null);
        arbiter = createInputArbiter({ state, frames, timers });
        activity = createActivityTracker();
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("starts dormant", () => {
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: WALK_ONLY,
            random: createSequenceRandom([]),
        });
        expect(controller.phase()).toStrictEqual({ kind: "dormant" });
    });
    it("stays dormant before the idle delay elapses", () => {
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: WALK_ONLY,
            random: createSequenceRandom([]),
        });
        controller.update(0.5);
        expect(controller.phase().kind).toBe("dormant");
        expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
    });
    it("takes over and walks the bunny once the user has been idle", () => {
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: WALK_ONLY,
            random: createSequenceRandom([0, 0.5, 0.5, 0.5]),
        });
        controller.update(0.5);
        controller.update(0.6);
        expect(controller.phase().kind).toBe("walk");
        expect(state.intent).toStrictEqual(createIntent("left", null));
        vi.advanceTimersByTime(500);
        expect(bunny.animation.kind).toBe("walk");
    });
    it("accumulates idle time while the user holds nothing", () => {
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: WALK_ONLY,
            random: createSequenceRandom([0, 0.5, 0.5, 0.5]),
        });
        controller.update(0.4);
        controller.update(0.4);
        expect(activity.idleSeconds()).toBeCloseTo(0.8);
    });
    it("keeps the idle timer pinned while the user holds an input", () => {
        arbiter.submit("user", createIntent("right", null));
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: WALK_ONLY,
            random: createSequenceRandom([]),
        });
        controller.update(5);
        controller.update(5);
        expect(activity.idleSeconds()).toBe(0);
        expect(controller.phase().kind).toBe("dormant");
    });
    it("stands down again when the user takes over mid-leg", () => {
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: WALK_ONLY,
            random: createSequenceRandom([0, 0.5, 0.5, 0.5]),
        });
        controller.update(1.5);
        expect(controller.phase().kind).toBe("walk");
        arbiter.submit("user", createIntent("right", null));
        controller.update(0.1);
        expect(controller.phase().kind).toBe("dormant");
        expect(arbiter.intentFor("autopilot")).toStrictEqual(NEUTRAL_INTENT);
        expect(state.intent).toStrictEqual(createIntent("right", null));
    });
    it("releases the world back to a standstill after standing down", () => {
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: WALK_ONLY,
            random: createSequenceRandom([0, 0.5, 0.5, 0.5]),
        });
        controller.update(1.5);
        activity.record();
        controller.update(0.1);
        arbiter.submit("user", NEUTRAL_INTENT);
        expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
    });
    it("jumps mid-leg and keeps walking through the air", () => {
        // Draws: leg 4s, walk, keep direction, jump roll hits, jump at the 2s mark.
        const alwaysJump = { ...WALK_ONLY, jumpChance: 1 };
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: alwaysJump,
            random: createSequenceRandom([0, 0.5, 0.5, 0.5, 0.5]),
        });
        controller.update(1.5);
        vi.advanceTimersByTime(500);
        expect(bunny.animation.kind).toBe("walk");
        controller.update(2.5);
        expect(bunny.animation.kind).toBe("jump");
        // The leg continues: still walking, intent still held, so the world keeps
        // scrolling instead of stopping dead in mid-air.
        expect(controller.phase().kind).toBe("walk");
        expect(state.intent).toStrictEqual(createIntent("left", null));
    });
    it("jumps only once per leg", () => {
        const alwaysJump = { ...WALK_ONLY, jumpChance: 1 };
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: alwaysJump,
            random: createSequenceRandom([0, 0.5, 0.5, 0.5, 0.5]),
        });
        controller.update(1.5);
        controller.update(2.5);
        expect(bunny.animation.kind).toBe("jump");
        bunny.animation = { kind: "walk", frameIdx: 0 };
        controller.update(0.5);
        expect(bunny.animation.kind).toBe("walk");
    });
    it("does not jump when the jump roll fails", () => {
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: WALK_ONLY,
            random: createSequenceRandom([0, 0.5, 0.5, 0.5, 0.5]),
        });
        controller.update(1.5);
        vi.advanceTimersByTime(500);
        controller.update(4);
        expect(bunny.animation.kind).not.toBe("jump");
        expect(controller.phase().kind).toBe("pause");
    });
    it("hops into depth when the hop roll succeeds", () => {
        const alwaysHop = { ...WALK_ONLY, hopChance: 1 };
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: alwaysHop,
            random: createSequenceRandom([0, 0.5, 0.2]),
        });
        controller.update(1.5);
        expect(controller.phase().kind).toBe("hop");
        expect(state.intent).toStrictEqual(createIntent(null, "up"));
        vi.advanceTimersByTime(500);
        expect(bunny.animation.kind).toBe("hop");
    });
    it("stays put entirely when autorun is disabled", () => {
        const disabled = { ...WALK_ONLY, enabled: false };
        const controller = createAutopilotController({
            arbiter,
            activity,
            state,
            config: disabled,
            random: createSequenceRandom([]),
        });
        controller.update(60);
        controller.update(60);
        expect(controller.phase().kind).toBe("dormant");
        expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
        expect(bunny.animation).toStrictEqual({ kind: "idle", frameIdx: 0 });
    });
});
//# sourceMappingURL=controller.test.js.map