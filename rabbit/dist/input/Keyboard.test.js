/**
 * @vitest-environment jsdom
 * Tests for the keyboard input source.
 *
 * The keyboard is driven through real KeyboardEvent objects and a real
 * arbiter, so assertions are on the intent that reaches engine state.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { _test_hooks } from "./Keyboard.js";
import { createInputArbiter } from "./arbiter.js";
import { createActivityTracker } from "./activity.js";
import { NEUTRAL_INTENT, createIntent } from "./intent.js";
import { DEFAULT_CAMERA_Z } from "../world/Projection.js";
import { createTestBunnyState, createTestFrames, createTestInputState, createTestKeyboardSource, createTestTimers, } from "../testing/fixtures.js";
const { createKeyboardKeys, intentFromKeys, pressBinding, releaseBinding, handleKeyDown, handleKeyUp, setupKeyboardControls, KEY_BINDINGS, } = _test_hooks;
describe("createKeyboardKeys", () => {
    it("starts with nothing held", () => {
        expect(createKeyboardKeys()).toStrictEqual({ horizontal: null, vertical: null });
    });
});
describe("intentFromKeys", () => {
    it("mirrors the held keys onto both axes", () => {
        expect(intentFromKeys({ horizontal: "left", vertical: "down" })).toStrictEqual(createIntent("left", "down"));
    });
    it("is neutral when nothing is held", () => {
        expect(intentFromKeys({ horizontal: null, vertical: null })).toStrictEqual(NEUTRAL_INTENT);
    });
});
describe("KEY_BINDINGS", () => {
    it("binds both the arrow keys and WASD", () => {
        expect(KEY_BINDINGS.get("arrowleft")).toStrictEqual({ axis: "horizontal", value: "left" });
        expect(KEY_BINDINGS.get("a")).toStrictEqual({ axis: "horizontal", value: "left" });
        expect(KEY_BINDINGS.get("arrowright")).toStrictEqual({ axis: "horizontal", value: "right" });
        expect(KEY_BINDINGS.get("d")).toStrictEqual({ axis: "horizontal", value: "right" });
        expect(KEY_BINDINGS.get("arrowup")).toStrictEqual({ axis: "vertical", value: "up" });
        expect(KEY_BINDINGS.get("w")).toStrictEqual({ axis: "vertical", value: "up" });
        expect(KEY_BINDINGS.get("arrowdown")).toStrictEqual({ axis: "vertical", value: "down" });
        expect(KEY_BINDINGS.get("s")).toStrictEqual({ axis: "vertical", value: "down" });
    });
    it("does not bind unrelated keys", () => {
        expect(KEY_BINDINGS.get("q")).toBeUndefined();
    });
});
describe("pressBinding", () => {
    it("sets the horizontal axis", () => {
        const keys = { horizontal: null, vertical: null };
        pressBinding(keys, { axis: "horizontal", value: "right" });
        expect(keys).toStrictEqual({ horizontal: "right", vertical: null });
    });
    it("sets the vertical axis", () => {
        const keys = { horizontal: null, vertical: null };
        pressBinding(keys, { axis: "vertical", value: "down" });
        expect(keys).toStrictEqual({ horizontal: null, vertical: "down" });
    });
    it("replaces the direction already held on an axis", () => {
        const keys = { horizontal: "left", vertical: null };
        pressBinding(keys, { axis: "horizontal", value: "right" });
        expect(keys.horizontal).toBe("right");
    });
});
describe("releaseBinding", () => {
    it("clears the horizontal axis when the held direction is released", () => {
        const keys = { horizontal: "left", vertical: null };
        expect(releaseBinding(keys, { axis: "horizontal", value: "left" })).toBe(true);
        expect(keys.horizontal).toBeNull();
    });
    it("ignores release of a horizontal direction that was overridden", () => {
        const keys = { horizontal: "right", vertical: null };
        expect(releaseBinding(keys, { axis: "horizontal", value: "left" })).toBe(false);
        expect(keys.horizontal).toBe("right");
    });
    it("clears the vertical axis when the held direction is released", () => {
        const keys = { horizontal: null, vertical: "up" };
        expect(releaseBinding(keys, { axis: "vertical", value: "up" })).toBe(true);
        expect(keys.vertical).toBeNull();
    });
    it("ignores release of a vertical direction that was overridden", () => {
        const keys = { horizontal: null, vertical: "down" };
        expect(releaseBinding(keys, { axis: "vertical", value: "up" })).toBe(false);
        expect(keys.vertical).toBe("down");
    });
});
describe("keyboard source", () => {
    let bunny;
    let state;
    let frames;
    let timers;
    let arbiter;
    let activity;
    let events;
    let deps;
    beforeEach(() => {
        vi.useFakeTimers();
        bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        state = createTestInputState(bunny);
        frames = createTestFrames();
        timers = createTestTimers(bunny, frames, () => state.intent.horizontal !== null);
        arbiter = createInputArbiter({ state, frames, timers });
        activity = createActivityTracker();
        events = createTestKeyboardSource();
        deps = { state, arbiter, activity, events };
        setupKeyboardControls(deps);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("binds one listener for each of keydown and keyup", () => {
        expect(events.boundCount("keydown")).toBe(1);
        expect(events.boundCount("keyup")).toBe(1);
    });
    describe("movement keys", () => {
        it("submits a left intent for ArrowLeft", () => {
            events.press("ArrowLeft");
            expect(state.intent).toStrictEqual(createIntent("left", null));
        });
        it("submits a left intent for the a key", () => {
            events.press("a");
            expect(state.intent).toStrictEqual(createIntent("left", null));
        });
        it("treats an uppercase key the same as lowercase", () => {
            events.press("D");
            expect(state.intent).toStrictEqual(createIntent("right", null));
        });
        it("submits an up intent for w", () => {
            events.press("w");
            expect(state.intent).toStrictEqual(createIntent(null, "up"));
        });
        it("submits a down intent for ArrowDown", () => {
            events.press("ArrowDown");
            expect(state.intent).toStrictEqual(createIntent(null, "down"));
        });
        it("combines both axes when two keys are held", () => {
            events.press("d");
            events.press("w");
            expect(state.intent).toStrictEqual(createIntent("right", "up"));
        });
        it("clears the axis on release", () => {
            events.press("d");
            events.release("d");
            expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
        });
        it("keeps walking when a superseded key is released", () => {
            events.press("a");
            events.press("d");
            events.release("a");
            expect(state.intent).toStrictEqual(createIntent("right", null));
        });
        it("drives the bunny into a real walk", () => {
            events.press("d");
            vi.advanceTimersByTime(500);
            expect(bunny.animation.kind).toBe("walk");
            expect(bunny.facingRight).toBe(true);
        });
        it("ignores auto-repeat so a held key does not restart the walk", () => {
            events.press("d");
            vi.advanceTimersByTime(500);
            const walking = { ...bunny.animation };
            events.press("d", true);
            expect(bunny.animation).toStrictEqual(walking);
        });
        it("ignores unbound keys", () => {
            events.press("q");
            expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
        });
        it("ignores release of an unbound key", () => {
            events.press("d");
            events.release("q");
            expect(state.intent).toStrictEqual(createIntent("right", null));
        });
    });
    describe("action keys", () => {
        it("jumps on space and prevents the page from scrolling", () => {
            const event = events.press(" ");
            expect(event.defaultPrevented).toBe(true);
            // Jumping from idle runs the transition first, then a single jump frame.
            vi.advanceTimersByTime(250);
            expect(bunny.animation.kind).toBe("jump");
        });
        it("does not change movement intent when jumping", () => {
            events.press(" ");
            expect(state.intent).toStrictEqual(NEUTRAL_INTENT);
        });
        it("resets the camera on r", () => {
            state.camera = { x: 250, z: 40 };
            events.press("r");
            expect(state.camera).toStrictEqual({ x: 0, z: DEFAULT_CAMERA_Z });
        });
        it("leaves movement intent untouched when resetting the camera", () => {
            events.press("d");
            events.press("r");
            expect(state.intent).toStrictEqual(createIntent("right", null));
        });
    });
    describe("activity reporting", () => {
        it("records activity for a movement key", () => {
            activity.advance(9);
            events.press("d");
            expect(activity.idleSeconds()).toBe(0);
        });
        it("records activity for an unbound key", () => {
            activity.advance(9);
            events.press("q");
            expect(activity.idleSeconds()).toBe(0);
        });
        it("records activity for auto-repeat of a held key", () => {
            events.press("d");
            activity.advance(9);
            events.press("d", true);
            expect(activity.idleSeconds()).toBe(0);
        });
        it("records activity on release", () => {
            events.press("d");
            activity.advance(9);
            events.release("d");
            expect(activity.idleSeconds()).toBe(0);
        });
        it("does not record activity for a release that changes nothing", () => {
            events.press("d");
            activity.advance(9);
            events.release("a");
            expect(activity.idleSeconds()).toBe(9);
        });
    });
    describe("direct handler invocation", () => {
        it("handleKeyDown updates the supplied key model", () => {
            const keys = createKeyboardKeys();
            handleKeyDown(new KeyboardEvent("keydown", { key: "a" }), keys, deps);
            expect(keys.horizontal).toBe("left");
        });
        it("handleKeyUp updates the supplied key model", () => {
            const keys = { horizontal: "left", vertical: null };
            handleKeyUp(new KeyboardEvent("keyup", { key: "a" }), keys, deps);
            expect(keys.horizontal).toBeNull();
        });
    });
});
//# sourceMappingURL=Keyboard.test.js.map