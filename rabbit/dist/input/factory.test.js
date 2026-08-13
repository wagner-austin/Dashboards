/**
 * @vitest-environment jsdom
 * Integration tests for the assembled input layer.
 *
 * These exercise the whole layer end to end: real keyboard and touch sources,
 * real arbitration, the real autopilot, and the real bunny state machine. The
 * assertions are on where the bunny ends up and where the camera moved.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { _test_hooks } from "./factory.js";
import { NEUTRAL_INTENT, createIntent } from "./intent.js";
import { DEFAULT_TOUCH_CONFIG } from "./Touch.js";
import { createConstantRandom, createTestBunnyState, createTestFrames, createTestInputState, createTestKeyboardSource, createTestTimers, createTestTouchSource, } from "../testing/fixtures.js";
const { createInputSystem } = _test_hooks;
/** Engages after one second idle and only ever walks right. */
const WALK_RIGHT = {
    enabled: true,
    idleDelay: 1,
    minLeg: 10,
    maxLeg: 10,
    minPause: 1,
    maxPause: 1,
    turnChance: 0,
    hopChance: 0,
    jumpChance: 0,
};
describe("createInputSystem", () => {
    let bunny;
    let state;
    let frames;
    let timers;
    let keyboardEvents;
    let touchEvents;
    let system;
    /**
     * Assemble the input layer around the shared fixtures.
     *
     * Args:
     *     autorun: Autorun configuration to run with.
     *
     * Returns:
     *     The assembled input system.
     */
    function build(autorun) {
        return createInputSystem({
            state,
            frames,
            timers,
            autorun,
            random: createConstantRandom(0.5),
            keyboardEvents,
            touchEvents,
            touch: DEFAULT_TOUCH_CONFIG,
        });
    }
    beforeEach(() => {
        vi.useFakeTimers();
        bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 }, true);
        state = createTestInputState(bunny);
        frames = createTestFrames();
        timers = createTestTimers(bunny, frames, () => state.intent.horizontal !== null);
        keyboardEvents = createTestKeyboardSource();
        touchEvents = createTestTouchSource();
        system = build(WALK_RIGHT);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("binds both input sources", () => {
        expect(keyboardEvents.boundCount("keydown")).toBe(1);
        expect(keyboardEvents.boundCount("keyup")).toBe(1);
        expect(touchEvents.passiveFor("touchmove")).toBe(false);
    });
    it("exposes the assembled services", () => {
        expect(system.arbiter.intentFor("user")).toStrictEqual(NEUTRAL_INTENT);
        expect(system.activity.idleSeconds()).toBe(0);
        expect(system.autopilot.phase().kind).toBe("dormant");
        expect(system.keys).toStrictEqual({ horizontal: null, vertical: null });
        expect(system.touchState.joystick).toBeNull();
    });
    it("scrolls the camera while the user walks", () => {
        keyboardEvents.press("d");
        vi.advanceTimersByTime(500);
        system.update(1);
        expect(bunny.animation.kind).toBe("walk");
        expect(state.camera.x).toBeGreaterThan(0);
    });
    it("moves the camera through depth while the user hops", () => {
        keyboardEvents.press("w");
        vi.advanceTimersByTime(500);
        system.update(1);
        expect(bunny.animation.kind).toBe("hop");
        expect(state.camera.z).not.toBe(0);
    });
    it("hands control to the autopilot after the idle delay", () => {
        system.update(0.5);
        expect(system.autopilot.phase().kind).toBe("dormant");
        system.update(0.6);
        expect(system.autopilot.phase().kind).toBe("walk");
        expect(state.intent).toStrictEqual(createIntent("right", null));
    });
    it("walks the bunny and scrolls the world with nobody at the keyboard", () => {
        system.update(1.5);
        vi.advanceTimersByTime(500);
        system.update(0.5);
        expect(bunny.animation.kind).toBe("walk");
        expect(state.camera.x).toBeGreaterThan(0);
    });
    it("gives control straight back the moment a key is pressed", () => {
        system.update(1.5);
        expect(state.intent).toStrictEqual(createIntent("right", null));
        keyboardEvents.press("a");
        expect(state.intent).toStrictEqual(createIntent("left", null));
        system.update(0.016);
        expect(system.autopilot.phase().kind).toBe("dormant");
        expect(state.intent).toStrictEqual(createIntent("left", null));
    });
    it("stops the bunny when the user releases after taking over", () => {
        system.update(1.5);
        keyboardEvents.press("a");
        system.update(0.016);
        keyboardEvents.release("a");
        system.update(0.016);
        expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
        expect(system.autopilot.phase().kind).toBe("dormant");
    });
    it("takes over again once the user goes quiet", () => {
        keyboardEvents.press("a");
        keyboardEvents.release("a");
        system.update(0.5);
        expect(system.autopilot.phase().kind).toBe("dormant");
        system.update(0.6);
        expect(system.autopilot.phase().kind).toBe("walk");
    });
    it("gives control back on a touch as well as a key", () => {
        system.update(1.5);
        expect(system.autopilot.phase().kind).toBe("walk");
        touchEvents.emit("touchstart", [{ identifier: 1, clientX: 100, clientY: 100 }]);
        touchEvents.emit("touchmove", [{ identifier: 1, clientX: 20, clientY: 100 }]);
        expect(state.intent).toStrictEqual(createIntent("left", null));
        system.update(0.016);
        expect(system.autopilot.phase().kind).toBe("dormant");
    });
    it("never engages when autorun is disabled", () => {
        const disabled = { ...WALK_RIGHT, enabled: false };
        const quiet = build(disabled);
        quiet.update(60);
        quiet.update(60);
        expect(quiet.autopilot.phase().kind).toBe("dormant");
        expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
        expect(state.camera.x).toBe(0);
    });
});
//# sourceMappingURL=factory.test.js.map