/**
 * @vitest-environment jsdom
 * Tests for the touch input source.
 *
 * The joystick works on plain touch points, so these tests supply real point
 * values and assert on the intent that reaches engine state.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { DEFAULT_TOUCH_CONFIG, _test_hooks, } from "./Touch.js";
import { createInputArbiter } from "./arbiter.js";
import { createActivityTracker } from "./activity.js";
import { NEUTRAL_INTENT, createIntent } from "./intent.js";
import { createTestBunnyState, createTestFrames, createTestInputState, createTestTimers, createTestTouchSource, } from "../testing/fixtures.js";
const { createTouchState, calculateDirection, isTap, directionToHorizontal, directionToVertical, directionToIntent, processDirectionChange, handleTouchEnd, handleTouchStart, handleTouchMove, handleTouchEndEvent, findTouchByIdentifier, setupTouchControls, } = _test_hooks;
/**
 * Build a joystick anchored at the origin and dragged to a point.
 *
 * Args:
 *     dx: Horizontal drag distance.
 *     dy: Vertical drag distance.
 *     startTime: Timestamp the touch began.
 *
 * Returns:
 *     JoystickState reflecting that drag.
 */
function joystickAt(dx, dy, startTime = 0) {
    return {
        anchorX: 100,
        anchorY: 100,
        currentX: 100 + dx,
        currentY: 100 + dy,
        startTime,
        identifier: 1,
    };
}
/**
 * Build a touch point.
 *
 * Args:
 *     identifier: Touch identifier.
 *     clientX: Horizontal position.
 *     clientY: Vertical position.
 *
 * Returns:
 *     A TouchPoint with those values.
 */
function point(identifier, clientX, clientY) {
    return { identifier, clientX, clientY };
}
describe("createTouchState", () => {
    it("starts with no joystick and no direction", () => {
        expect(createTouchState()).toStrictEqual({ joystick: null, currentDirection: null });
    });
});
describe("calculateDirection", () => {
    it("is null inside the deadzone", () => {
        expect(calculateDirection(joystickAt(5, 5), DEFAULT_TOUCH_CONFIG)).toBeNull();
    });
    it("resolves the four cardinal directions", () => {
        expect(calculateDirection(joystickAt(50, 0), DEFAULT_TOUCH_CONFIG)).toBe("right");
        expect(calculateDirection(joystickAt(-50, 0), DEFAULT_TOUCH_CONFIG)).toBe("left");
        expect(calculateDirection(joystickAt(0, -50), DEFAULT_TOUCH_CONFIG)).toBe("up");
        expect(calculateDirection(joystickAt(0, 50), DEFAULT_TOUCH_CONFIG)).toBe("down");
    });
    it("resolves the four diagonals", () => {
        expect(calculateDirection(joystickAt(50, -50), DEFAULT_TOUCH_CONFIG)).toBe("up-right");
        expect(calculateDirection(joystickAt(-50, -50), DEFAULT_TOUCH_CONFIG)).toBe("up-left");
        expect(calculateDirection(joystickAt(-50, 50), DEFAULT_TOUCH_CONFIG)).toBe("down-left");
        expect(calculateDirection(joystickAt(50, 50), DEFAULT_TOUCH_CONFIG)).toBe("down-right");
    });
    it("registers a drag exactly at the deadzone edge", () => {
        expect(calculateDirection(joystickAt(DEFAULT_TOUCH_CONFIG.deadzone, 0), DEFAULT_TOUCH_CONFIG)).toBe("right");
    });
});
describe("direction decomposition", () => {
    it("extracts the horizontal component", () => {
        expect(directionToHorizontal(null)).toBeNull();
        expect(directionToHorizontal("left")).toBe("left");
        expect(directionToHorizontal("up-right")).toBe("right");
        expect(directionToHorizontal("up")).toBeNull();
    });
    it("extracts the vertical component", () => {
        expect(directionToVertical(null)).toBeNull();
        expect(directionToVertical("up")).toBe("up");
        expect(directionToVertical("down-left")).toBe("down");
        expect(directionToVertical("right")).toBeNull();
    });
    it("builds an intent from a diagonal", () => {
        expect(directionToIntent("down-left")).toStrictEqual(createIntent("left", "down"));
    });
    it("builds a neutral intent from no direction", () => {
        expect(directionToIntent(null)).toStrictEqual(NEUTRAL_INTENT);
    });
});
describe("isTap", () => {
    it("accepts a quick, still touch", () => {
        expect(isTap(joystickAt(2, 2), 100, DEFAULT_TOUCH_CONFIG)).toBe(true);
    });
    it("rejects a touch held too long", () => {
        expect(isTap(joystickAt(2, 2), 500, DEFAULT_TOUCH_CONFIG)).toBe(false);
    });
    it("rejects a touch that moved too far", () => {
        expect(isTap(joystickAt(80, 0), 100, DEFAULT_TOUCH_CONFIG)).toBe(false);
    });
});
describe("findTouchByIdentifier", () => {
    it("finds a tracked point", () => {
        expect(findTouchByIdentifier([point(1, 5, 5), point(2, 9, 9)], 2)).toStrictEqual(point(2, 9, 9));
    });
    it("returns undefined when the point is gone", () => {
        expect(findTouchByIdentifier([point(1, 5, 5)], 2)).toBeUndefined();
    });
    it("returns undefined for no points at all", () => {
        expect(findTouchByIdentifier([], 1)).toBeUndefined();
    });
});
describe("handleTouchStart", () => {
    it("anchors a joystick at the touch point", () => {
        const touchState = createTouchState();
        expect(handleTouchStart(touchState, [point(7, 30, 40)], 123)).toBe(true);
        expect(touchState.joystick).toStrictEqual({
            anchorX: 30,
            anchorY: 40,
            currentX: 30,
            currentY: 40,
            startTime: 123,
            identifier: 7,
        });
    });
    it("ignores a second finger while a joystick is active", () => {
        const touchState = createTouchState();
        handleTouchStart(touchState, [point(7, 30, 40)], 0);
        expect(handleTouchStart(touchState, [point(8, 90, 90)], 5)).toBe(false);
        expect(touchState.joystick?.identifier).toBe(7);
    });
    it("does nothing when the event carries no points", () => {
        const touchState = createTouchState();
        expect(handleTouchStart(touchState, [], 0)).toBe(false);
        expect(touchState.joystick).toBeNull();
    });
});
describe("touch source", () => {
    let bunny;
    let state;
    let frames;
    let timers;
    let arbiter;
    let activity;
    let events;
    let deps;
    let touchState;
    beforeEach(() => {
        vi.useFakeTimers();
        bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        state = createTestInputState(bunny);
        frames = createTestFrames();
        timers = createTestTimers(bunny, frames, () => state.intent.horizontal !== null);
        arbiter = createInputArbiter({ state, frames, timers });
        activity = createActivityTracker();
        events = createTestTouchSource();
        deps = { arbiter, activity, events, config: DEFAULT_TOUCH_CONFIG };
        touchState = createTouchState();
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    describe("processDirectionChange", () => {
        it("submits the intent for the new direction", () => {
            processDirectionChange("left", touchState, deps);
            expect(state.intent).toStrictEqual(createIntent("left", null));
            expect(touchState.currentDirection).toBe("left");
        });
        it("records user activity", () => {
            activity.advance(9);
            processDirectionChange("left", touchState, deps);
            expect(activity.idleSeconds()).toBe(0);
        });
    });
    describe("handleTouchMove", () => {
        it("does nothing without an active joystick", () => {
            expect(handleTouchMove(touchState, deps, [point(1, 0, 0)])).toBe(false);
        });
        it("does nothing when the tracked finger is absent", () => {
            handleTouchStart(touchState, [point(1, 100, 100)], 0);
            expect(handleTouchMove(touchState, deps, [point(2, 150, 100)])).toBe(false);
        });
        it("consumes the gesture and submits intent when dragged", () => {
            handleTouchStart(touchState, [point(1, 100, 100)], 0);
            expect(handleTouchMove(touchState, deps, [point(1, 200, 100)])).toBe(true);
            expect(state.intent).toStrictEqual(createIntent("right", null));
        });
        it("consumes the gesture but submits nothing when the direction is unchanged", () => {
            handleTouchStart(touchState, [point(1, 100, 100)], 0);
            handleTouchMove(touchState, deps, [point(1, 200, 100)]);
            vi.advanceTimersByTime(500);
            const walking = { ...bunny.animation };
            expect(handleTouchMove(touchState, deps, [point(1, 210, 100)])).toBe(true);
            expect(bunny.animation).toStrictEqual(walking);
        });
        it("drives the bunny into a real walk", () => {
            handleTouchStart(touchState, [point(1, 100, 100)], 0);
            handleTouchMove(touchState, deps, [point(1, 200, 100)]);
            vi.advanceTimersByTime(500);
            expect(bunny.animation.kind).toBe("walk");
        });
    });
    describe("handleTouchEnd", () => {
        it("does nothing without an active joystick", () => {
            handleTouchEnd(touchState, deps, 100);
            expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
        });
        it("jumps on a tap", () => {
            handleTouchStart(touchState, [point(1, 100, 100)], 0);
            handleTouchEnd(touchState, deps, 50);
            // Jumping from idle runs the transition first, then a single jump frame.
            vi.advanceTimersByTime(250);
            expect(bunny.animation.kind).toBe("jump");
            expect(touchState.joystick).toBeNull();
        });
        it("releases movement after a drag", () => {
            handleTouchStart(touchState, [point(1, 100, 100)], 0);
            handleTouchMove(touchState, deps, [point(1, 200, 100)]);
            handleTouchEnd(touchState, deps, 50);
            expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
            expect(touchState.currentDirection).toBeNull();
        });
        it("records user activity", () => {
            handleTouchStart(touchState, [point(1, 100, 100)], 0);
            activity.advance(9);
            handleTouchEnd(touchState, deps, 50);
            expect(activity.idleSeconds()).toBe(0);
        });
    });
    describe("handleTouchEndEvent", () => {
        it("does nothing without an active joystick", () => {
            handleTouchEndEvent(touchState, deps, [], 100);
            expect(touchState.joystick).toBeNull();
        });
        it("keeps the joystick while the finger is still down", () => {
            handleTouchStart(touchState, [point(1, 100, 100)], 0);
            handleTouchEndEvent(touchState, deps, [point(1, 100, 100)], 50);
            expect(touchState.joystick).not.toBeNull();
        });
        it("ends the gesture once the finger is gone", () => {
            handleTouchStart(touchState, [point(1, 100, 100)], 0);
            handleTouchEndEvent(touchState, deps, [], 50);
            expect(touchState.joystick).toBeNull();
        });
    });
    describe("setupTouchControls", () => {
        it("binds all four touch events", () => {
            setupTouchControls(deps);
            expect(events.passiveFor("touchstart")).toBe(true);
            expect(events.passiveFor("touchmove")).toBe(false);
            expect(events.passiveFor("touchend")).toBe(true);
            expect(events.passiveFor("touchcancel")).toBe(true);
        });
        it("never consumes touchstart, so audio can unlock", () => {
            setupTouchControls(deps);
            expect(events.emit("touchstart", [point(1, 100, 100)])).toBe(false);
        });
        it("consumes touchmove once a joystick is active", () => {
            setupTouchControls(deps);
            events.emit("touchstart", [point(1, 100, 100)]);
            expect(events.emit("touchmove", [point(1, 200, 100)])).toBe(true);
            expect(state.intent).toStrictEqual(createIntent("right", null));
        });
        it("does not consume touchmove without a joystick", () => {
            setupTouchControls(deps);
            expect(events.emit("touchmove", [point(1, 200, 100)])).toBe(false);
        });
        it("ends the gesture on touchend without consuming it", () => {
            setupTouchControls(deps);
            events.emit("touchstart", [point(1, 100, 100)]);
            events.emit("touchmove", [point(1, 200, 100)]);
            events.setNow(50);
            expect(events.emit("touchend", [])).toBe(false);
            expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
        });
        it("ends the gesture on touchcancel", () => {
            const cancelled = setupTouchControls(deps);
            events.emit("touchstart", [point(1, 100, 100)]);
            events.emit("touchcancel", []);
            expect(cancelled.joystick).toBeNull();
        });
        it("uses the injected clock for tap detection", () => {
            setupTouchControls(deps);
            events.setNow(0);
            events.emit("touchstart", [point(1, 100, 100)]);
            events.setNow(1000);
            events.emit("touchend", []);
            vi.advanceTimersByTime(500);
            expect(bunny.animation.kind).not.toBe("jump");
        });
    });
});
//# sourceMappingURL=Touch.test.js.map