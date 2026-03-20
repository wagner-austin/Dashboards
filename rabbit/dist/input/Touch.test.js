/**
 * @vitest-environment happy-dom
 * Tests for touch input handling with unified input model.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createTouchState, calculateDirection, isTap, processDirectionChange, handleTouchEnd, handleTouchStart, handleTouchMove, handleTouchEndEvent, setupTouchControls, DEFAULT_TOUCH_CONFIG, _test_hooks, } from "./Touch.js";
import { createBunnyTimers } from "../entities/Bunny.js";
import { calculateDepthBounds, createProjectionConfig } from "../world/Projection.js";
import { layerToWorldZ } from "../layers/widths.js";
const { directionToHorizontal, directionToVertical } = _test_hooks;
function createTestDepthBounds() {
    const projectionConfig = createProjectionConfig();
    return calculateDepthBounds(layerToWorldZ(8), layerToWorldZ(30), projectionConfig);
}
const TEST_DEPTH_BOUNDS = createTestDepthBounds();
function createTestFrames() {
    return {
        walkLeft: ["wL0", "wL1"],
        walkRight: ["wR0", "wR1"],
        jumpLeft: ["jL0"],
        jumpRight: ["jR0"],
        idleLeft: ["iL0"],
        idleRight: ["iR0"],
        walkToIdleLeft: ["t0", "t1", "t2"],
        walkToIdleRight: ["t0", "t1", "t2"],
        walkToTurnAwayLeft: ["ta0", "ta1"],
        walkToTurnAwayRight: ["ta0", "ta1"],
        walkToTurnTowardLeft: ["tt0", "tt1"],
        walkToTurnTowardRight: ["tt0", "tt1"],
        hopAway: ["ha0", "ha1"],
        hopToward: ["ht0", "ht1"],
    };
}
function createTestBunnyState(animation) {
    return { facingRight: false, animation };
}
function createTestInputState(bunny) {
    return {
        bunny,
        viewport: { width: 100, height: 50, charW: 10, charH: 20 },
        camera: { x: 0, z: 0 },
        depthBounds: TEST_DEPTH_BOUNDS,
        horizontalHeld: null,
        verticalHeld: null,
    };
}
function createJoystick(dx, dy, startTime = 0) {
    return {
        anchorX: 100,
        anchorY: 100,
        currentX: 100 + dx,
        currentY: 100 + dy,
        startTime,
        identifier: 0,
    };
}
/**
 * Create mock TouchList for testing.
 */
function createMockTouchList(touches) {
    const list = touches.map(t => t);
    return Object.assign(list, {
        item: (i) => list[i] ?? null,
    });
}
describe("createTouchState", () => {
    it("creates initial state with no joystick", () => {
        const state = createTouchState();
        expect(state.joystick).toBe(null);
        expect(state.currentDirection).toBe(null);
    });
});
describe("calculateDirection", () => {
    const config = DEFAULT_TOUCH_CONFIG;
    it("returns null within deadzone", () => {
        expect(calculateDirection(createJoystick(0, 0), config)).toBe(null);
        expect(calculateDirection(createJoystick(10, 10), config)).toBe(null);
    });
    it("returns correct 8-way directions", () => {
        expect(calculateDirection(createJoystick(50, 0), config)).toBe("right");
        expect(calculateDirection(createJoystick(-50, 0), config)).toBe("left");
        expect(calculateDirection(createJoystick(0, -50), config)).toBe("up");
        expect(calculateDirection(createJoystick(0, 50), config)).toBe("down");
        expect(calculateDirection(createJoystick(50, -50), config)).toBe("up-right");
        expect(calculateDirection(createJoystick(-50, -50), config)).toBe("up-left");
        expect(calculateDirection(createJoystick(50, 50), config)).toBe("down-right");
        expect(calculateDirection(createJoystick(-50, 50), config)).toBe("down-left");
    });
    it("handles boundary angles correctly", () => {
        expect(calculateDirection(createJoystick(50, 10), config)).toBe("right");
        expect(calculateDirection(createJoystick(50, -10), config)).toBe("right");
        expect(calculateDirection(createJoystick(10, -50), config)).toBe("up");
        expect(calculateDirection(createJoystick(-10, -50), config)).toBe("up");
    });
});
describe("directionToHorizontal", () => {
    it("extracts left from directions containing left", () => {
        expect(directionToHorizontal("left")).toBe("left");
        expect(directionToHorizontal("up-left")).toBe("left");
        expect(directionToHorizontal("down-left")).toBe("left");
    });
    it("extracts right from directions containing right", () => {
        expect(directionToHorizontal("right")).toBe("right");
        expect(directionToHorizontal("up-right")).toBe("right");
        expect(directionToHorizontal("down-right")).toBe("right");
    });
    it("returns null for pure vertical or null", () => {
        expect(directionToHorizontal("up")).toBe(null);
        expect(directionToHorizontal("down")).toBe(null);
        expect(directionToHorizontal(null)).toBe(null);
    });
});
describe("directionToVertical", () => {
    it("extracts up from directions containing up", () => {
        expect(directionToVertical("up")).toBe("up");
        expect(directionToVertical("up-left")).toBe("up");
        expect(directionToVertical("up-right")).toBe("up");
    });
    it("extracts down from directions containing down", () => {
        expect(directionToVertical("down")).toBe("down");
        expect(directionToVertical("down-left")).toBe("down");
        expect(directionToVertical("down-right")).toBe("down");
    });
    it("returns null for pure horizontal or null", () => {
        expect(directionToVertical("left")).toBe(null);
        expect(directionToVertical("right")).toBe(null);
        expect(directionToVertical(null)).toBe(null);
    });
});
describe("isTap", () => {
    const config = DEFAULT_TOUCH_CONFIG;
    it("returns true for quick touch with minimal movement", () => {
        expect(isTap(createJoystick(5, 5, 1000), 1100, config)).toBe(true);
        expect(isTap(createJoystick(0, 0, 1000), 1050, config)).toBe(true);
    });
    it("returns false for long touch or too much movement", () => {
        expect(isTap(createJoystick(5, 5, 1000), 1300, config)).toBe(false);
        expect(isTap(createJoystick(50, 0, 1000), 1100, config)).toBe(false);
    });
});
describe("processDirectionChange", () => {
    let inputState;
    let touchState;
    let timers;
    let frames;
    beforeEach(() => {
        vi.useFakeTimers();
        inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
        touchState = createTouchState();
        frames = createTestFrames();
        timers = createBunnyTimers(inputState.bunny, frames, {
            walk: 100, idle: 200, jump: 50, transition: 80, hop: 100,
        }, () => false);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("sets verticalHeld when moving up/down", () => {
        processDirectionChange(null, "up", touchState, inputState, frames, timers);
        expect(inputState.verticalHeld).toBe("up");
        inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
        touchState = createTouchState();
        processDirectionChange(null, "down", touchState, inputState, frames, timers);
        expect(inputState.verticalHeld).toBe("down");
    });
    it("sets horizontalHeld when moving left/right", () => {
        processDirectionChange(null, "left", touchState, inputState, frames, timers);
        expect(inputState.horizontalHeld).toBe("left");
        inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
        touchState = createTouchState();
        processDirectionChange(null, "right", touchState, inputState, frames, timers);
        expect(inputState.horizontalHeld).toBe("right");
    });
    it("sets both inputs for diagonal movement", () => {
        processDirectionChange(null, "up-right", touchState, inputState, frames, timers);
        expect(inputState.horizontalHeld).toBe("right");
        expect(inputState.verticalHeld).toBe("up");
    });
    it("clears inputs when returning to deadzone", () => {
        processDirectionChange(null, "up-right", touchState, inputState, frames, timers);
        expect(inputState.horizontalHeld).toBe("right");
        expect(inputState.verticalHeld).toBe("up");
        processDirectionChange("up-right", null, touchState, inputState, frames, timers);
        expect(inputState.horizontalHeld).toBe(null);
        expect(inputState.verticalHeld).toBe(null);
    });
    it("starts hop transition when vertical input begins", () => {
        processDirectionChange(null, "up", touchState, inputState, frames, timers);
        expect(inputState.bunny.animation.kind).toBe("transition");
    });
    it("starts walk when horizontal input without vertical", () => {
        processDirectionChange(null, "left", touchState, inputState, frames, timers);
        expect(inputState.bunny.animation.kind).toBe("transition");
        expect(inputState.bunny.facingRight).toBe(false);
    });
    it("switches walk direction from left to right", () => {
        processDirectionChange(null, "left", touchState, inputState, frames, timers);
        expect(inputState.horizontalHeld).toBe("left");
        processDirectionChange("left", "right", touchState, inputState, frames, timers);
        expect(inputState.horizontalHeld).toBe("right");
        expect(inputState.bunny.facingRight).toBe(true);
    });
    it("switches walk direction from right to left", () => {
        processDirectionChange(null, "right", touchState, inputState, frames, timers);
        expect(inputState.horizontalHeld).toBe("right");
        processDirectionChange("right", "left", touchState, inputState, frames, timers);
        expect(inputState.horizontalHeld).toBe("left");
        expect(inputState.bunny.facingRight).toBe(false);
    });
    it("updates touchState.currentDirection", () => {
        processDirectionChange(null, "up-left", touchState, inputState, frames, timers);
        expect(touchState.currentDirection).toBe("up-left");
    });
});
describe("handleTouchEnd", () => {
    let inputState;
    let touchState;
    let timers;
    let frames;
    const config = DEFAULT_TOUCH_CONFIG;
    beforeEach(() => {
        vi.useFakeTimers();
        inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
        touchState = createTouchState();
        frames = createTestFrames();
        timers = createBunnyTimers(inputState.bunny, frames, {
            walk: 100, idle: 200, jump: 50, transition: 80, hop: 100,
        }, () => false);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("does nothing if no joystick", () => {
        handleTouchEnd(touchState, inputState, frames, timers, Date.now(), config);
        expect(inputState.bunny.animation.kind).toBe("idle");
    });
    it("triggers jump on tap", () => {
        touchState.joystick = createJoystick(0, 0, Date.now() - 100);
        handleTouchEnd(touchState, inputState, frames, timers, Date.now(), config);
        expect(inputState.bunny.animation.kind).toBe("transition");
    });
    it("does not trigger jump on tap while hopping", () => {
        touchState.joystick = createJoystick(0, 0, Date.now() - 100);
        inputState.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0 };
        handleTouchEnd(touchState, inputState, frames, timers, Date.now(), config);
        expect(inputState.bunny.animation.kind).toBe("hop");
    });
    it("clears inputs on drag release", () => {
        touchState.joystick = createJoystick(50, 0, Date.now() - 300);
        inputState.horizontalHeld = "right";
        handleTouchEnd(touchState, inputState, frames, timers, Date.now(), config);
        expect(inputState.horizontalHeld).toBe(null);
    });
    it("clears vertical input on drag release", () => {
        touchState.joystick = createJoystick(0, -50, Date.now() - 300);
        inputState.verticalHeld = "up";
        inputState.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0 };
        timers.hop.start();
        handleTouchEnd(touchState, inputState, frames, timers, Date.now(), config);
        expect(inputState.verticalHeld).toBe(null);
    });
    it("clears joystick and direction", () => {
        touchState.joystick = createJoystick(50, 0, Date.now() - 300);
        touchState.currentDirection = "right";
        handleTouchEnd(touchState, inputState, frames, timers, Date.now(), config);
        expect(touchState.joystick).toBe(null);
        expect(touchState.currentDirection).toBe(null);
    });
});
describe("handleTouchStart", () => {
    it("creates joystick at touch point", () => {
        const touchState = createTouchState();
        const touches = createMockTouchList([{ identifier: 5, clientX: 200, clientY: 300 }]);
        const handled = handleTouchStart(touchState, touches, 1000);
        expect(handled).toBe(true);
        expect(touchState.joystick).not.toBe(null);
        expect(touchState.joystick?.anchorX).toBe(200);
        expect(touchState.joystick?.anchorY).toBe(300);
        expect(touchState.joystick?.identifier).toBe(5);
    });
    it("ignores if joystick already exists", () => {
        const touchState = createTouchState();
        touchState.joystick = createJoystick(0, 0);
        const touches = createMockTouchList([{ identifier: 1, clientX: 50, clientY: 50 }]);
        const handled = handleTouchStart(touchState, touches, 1000);
        expect(handled).toBe(false);
        expect(touchState.joystick).not.toBe(null);
        expect(touchState.joystick.anchorX).toBe(100);
    });
    it("returns false for empty touch list", () => {
        const touchState = createTouchState();
        const touches = createMockTouchList([]);
        const handled = handleTouchStart(touchState, touches, 1000);
        expect(handled).toBe(false);
        expect(touchState.joystick).toBe(null);
    });
});
describe("handleTouchMove", () => {
    let inputState;
    let touchState;
    let timers;
    let frames;
    const config = DEFAULT_TOUCH_CONFIG;
    beforeEach(() => {
        vi.useFakeTimers();
        inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
        touchState = createTouchState();
        touchState.joystick = createJoystick(0, 0);
        frames = createTestFrames();
        timers = createBunnyTimers(inputState.bunny, frames, {
            walk: 100, idle: 200, jump: 50, transition: 80, hop: 100,
        }, () => false);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("updates joystick position", () => {
        const touches = createMockTouchList([{ identifier: 0, clientX: 150, clientY: 100 }]);
        handleTouchMove(touchState, inputState, frames, timers, touches, config);
        expect(touchState.joystick?.currentX).toBe(150);
        expect(touchState.joystick?.currentY).toBe(100);
    });
    it("triggers direction change when moving out of deadzone", () => {
        const touches = createMockTouchList([{ identifier: 0, clientX: 150, clientY: 100 }]);
        handleTouchMove(touchState, inputState, frames, timers, touches, config);
        expect(touchState.currentDirection).toBe("right");
        expect(inputState.horizontalHeld).toBe("right");
    });
    it("returns false if no joystick", () => {
        touchState.joystick = null;
        const touches = createMockTouchList([{ identifier: 0, clientX: 150, clientY: 100 }]);
        const handled = handleTouchMove(touchState, inputState, frames, timers, touches, config);
        expect(handled).toBe(false);
    });
    it("returns false if touch not found", () => {
        const touches = createMockTouchList([{ identifier: 99, clientX: 150, clientY: 100 }]);
        const handled = handleTouchMove(touchState, inputState, frames, timers, touches, config);
        expect(handled).toBe(false);
    });
});
describe("handleTouchEndEvent", () => {
    let inputState;
    let touchState;
    let timers;
    let frames;
    const config = DEFAULT_TOUCH_CONFIG;
    beforeEach(() => {
        vi.useFakeTimers();
        inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
        touchState = createTouchState();
        touchState.joystick = createJoystick(50, 0, Date.now() - 300);
        frames = createTestFrames();
        timers = createBunnyTimers(inputState.bunny, frames, {
            walk: 100, idle: 200, jump: 50, transition: 80, hop: 100,
        }, () => false);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("does nothing if joystick is null", () => {
        touchState.joystick = null;
        const touches = createMockTouchList([]);
        handleTouchEndEvent(touchState, inputState, frames, timers, touches, Date.now(), config);
        expect(inputState.bunny.animation.kind).toBe("idle");
    });
    it("ends touch if identifier no longer in list", () => {
        const touches = createMockTouchList([]);
        handleTouchEndEvent(touchState, inputState, frames, timers, touches, Date.now(), config);
        expect(touchState.joystick).toBe(null);
    });
    it("keeps touch if identifier still in list", () => {
        const touches = createMockTouchList([{ identifier: 0, clientX: 150, clientY: 100 }]);
        handleTouchEndEvent(touchState, inputState, frames, timers, touches, Date.now(), config);
        expect(touchState.joystick).not.toBe(null);
    });
});
describe("setupTouchControls", () => {
    let inputState;
    let frames;
    let timers;
    beforeEach(() => {
        vi.useFakeTimers();
        inputState = createTestInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }));
        frames = createTestFrames();
        timers = createBunnyTimers(inputState.bunny, frames, {
            walk: 100, idle: 200, jump: 50, transition: 80, hop: 100,
        }, () => false);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    /**
     * Create a TouchEvent with specified touches.
     */
    function createTouchEvent(type, touches) {
        const touchArray = touches.map(t => ({
            identifier: t.identifier,
            clientX: t.clientX,
            clientY: t.clientY,
            screenX: t.clientX,
            screenY: t.clientY,
            pageX: t.clientX,
            pageY: t.clientY,
            target: document.body,
            radiusX: 1,
            radiusY: 1,
            rotationAngle: 0,
            force: 1,
        }));
        const mockTouchList = {
            length: touchArray.length,
            item: (index) => touchArray[index] ?? null,
            [Symbol.iterator]: function* () {
                for (const touch of touchArray) {
                    yield touch;
                }
            },
        };
        for (let i = 0; i < touchArray.length; i++) {
            const touch = touchArray[i];
            if (touch !== undefined) {
                mockTouchList[i] = touch;
            }
        }
        const event = new TouchEvent(type, { cancelable: true });
        Object.defineProperty(event, "touches", { value: mockTouchList });
        return event;
    }
    it("creates joystick on touchstart", () => {
        const touchState = setupTouchControls(inputState, frames, timers);
        const event = createTouchEvent("touchstart", [{ identifier: 0, clientX: 100, clientY: 100 }]);
        document.dispatchEvent(event);
        expect(touchState.joystick).not.toBe(null);
        expect(touchState.joystick?.anchorX).toBe(100);
    });
    it("updates direction on touchmove", () => {
        const touchState = setupTouchControls(inputState, frames, timers);
        const startEvent = createTouchEvent("touchstart", [{ identifier: 0, clientX: 100, clientY: 100 }]);
        document.dispatchEvent(startEvent);
        const moveEvent = createTouchEvent("touchmove", [{ identifier: 0, clientX: 150, clientY: 100 }]);
        document.dispatchEvent(moveEvent);
        expect(touchState.currentDirection).toBe("right");
        expect(inputState.horizontalHeld).toBe("right");
    });
    it("clears state on touchend", () => {
        const touchState = setupTouchControls(inputState, frames, timers);
        const startEvent = createTouchEvent("touchstart", [{ identifier: 0, clientX: 100, clientY: 100 }]);
        document.dispatchEvent(startEvent);
        const moveEvent = createTouchEvent("touchmove", [{ identifier: 0, clientX: 150, clientY: 100 }]);
        document.dispatchEvent(moveEvent);
        const endEvent = createTouchEvent("touchend", []);
        document.dispatchEvent(endEvent);
        expect(touchState.joystick).toBe(null);
        expect(touchState.currentDirection).toBe(null);
    });
    it("clears state on touchcancel", () => {
        const touchState = setupTouchControls(inputState, frames, timers);
        const startEvent = createTouchEvent("touchstart", [{ identifier: 0, clientX: 100, clientY: 100 }]);
        document.dispatchEvent(startEvent);
        const cancelEvent = createTouchEvent("touchcancel", []);
        document.dispatchEvent(cancelEvent);
        expect(touchState.joystick).toBe(null);
    });
    it("ignores touchmove when no joystick active", () => {
        const touchState = setupTouchControls(inputState, frames, timers);
        const moveEvent = createTouchEvent("touchmove", [{ identifier: 0, clientX: 150, clientY: 100 }]);
        document.dispatchEvent(moveEvent);
        expect(touchState.joystick).toBe(null);
        expect(touchState.currentDirection).toBe(null);
    });
});
//# sourceMappingURL=Touch.test.js.map