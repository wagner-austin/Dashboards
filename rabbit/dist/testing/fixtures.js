/**
 * Shared test fixtures for the input layer.
 *
 * These are real implementations, not stand-ins: the frame data is real frame
 * data, the event sources really store and replay handlers, and the draw
 * source really returns the sequence it was given. Nothing here fakes the
 * behaviour under test - it only supplies inputs that would otherwise be
 * duplicated across every suite.
 */
import { createBunnyTimers, } from "../entities/Bunny.js";
import { createInputState } from "../input/state.js";
import { layerToWorldZ } from "../layers/widths.js";
import { calculateDepthBounds, createProjectionConfig } from "../world/Projection.js";
/**
 * Create bunny frames with distinguishable labels per animation.
 *
 * Returns:
 *     BunnyFrames whose entries identify the animation and index they came from.
 */
export function createTestFrames() {
    return {
        walkLeft: ["walkL0", "walkL1"],
        walkRight: ["walkR0", "walkR1"],
        jumpLeft: ["jumpL0"],
        jumpRight: ["jumpR0"],
        idleLeft: ["idleL0"],
        idleRight: ["idleR0"],
        walkToIdleLeft: ["transL0", "transL1", "transL2"],
        walkToIdleRight: ["transR0", "transR1", "transR2"],
        walkToTurnAwayLeft: ["turnAwayL0", "turnAwayL1"],
        walkToTurnAwayRight: ["turnAwayR0", "turnAwayR1"],
        walkToTurnTowardLeft: ["turnTowardL0", "turnTowardL1"],
        walkToTurnTowardRight: ["turnTowardR0", "turnTowardR1"],
        hopAway: ["hopAway0", "hopAway1"],
        hopToward: ["hopToward0", "hopToward1"],
    };
}
/**
 * Create bunny state in a chosen animation.
 *
 * Args:
 *     animation: Animation state to start in.
 *     facingRight: Direction the bunny faces.
 *
 * Returns:
 *     BunnyState in that animation.
 */
export function createTestBunnyState(animation, facingRight = false) {
    return { facingRight, animation };
}
/**
 * Create depth bounds matching the shipped layer range of 8 to 30.
 *
 * Returns:
 *     DepthBounds derived from the real projection maths.
 */
export function createTestDepthBounds() {
    const projectionConfig = createProjectionConfig();
    return calculateDepthBounds(layerToWorldZ(8), layerToWorldZ(30), projectionConfig);
}
/**
 * Create input state around a bunny, with a neutral intent.
 *
 * Args:
 *     bunny: Bunny state to wrap.
 *
 * Returns:
 *     InputState positioned at the origin.
 */
export function createTestInputState(bunny) {
    return createInputState(bunny, { width: 100, height: 50, charW: 10, charH: 20 }, { x: 0, z: 0 }, createTestDepthBounds());
}
/**
 * Create real bunny animation timers with short intervals.
 *
 * Args:
 *     bunny: Bunny state the timers advance.
 *     frames: Animation frames the timers step through.
 *     isHorizontalHeld: Callback deciding what completion settles into.
 *
 * Returns:
 *     BunnyTimers wired to the given state.
 */
export function createTestTimers(bunny, frames, isHorizontalHeld) {
    return createBunnyTimers(bunny, frames, { walk: 100, idle: 200, jump: 50, transition: 80, hop: 100 }, isHorizontalHeld);
}
/**
 * Create a draw source that replays a fixed sequence.
 *
 * Exhausting the sequence throws rather than wrapping or returning a default,
 * so a test that consumes more draws than it declared fails loudly instead of
 * silently exercising a different branch.
 *
 * Args:
 *     draws: Values to return in order.
 *
 * Returns:
 *     RandomSource over that sequence.
 *
 * Raises:
 *     Error: When called more times than there are draws.
 */
export function createSequenceRandom(draws) {
    let index = 0;
    return () => {
        const value = draws[index];
        if (value === undefined) {
            throw new Error(`sequence random exhausted after ${String(draws.length)} draws`);
        }
        index += 1;
        return value;
    };
}
/**
 * Create a draw source that always returns the same value.
 *
 * Args:
 *     value: Value to return for every draw.
 *
 * Returns:
 *     RandomSource returning that value.
 */
export function createConstantRandom(value) {
    return () => value;
}
/**
 * Create a keyboard event source backed by real KeyboardEvent objects.
 *
 * Returns:
 *     TestKeyboardSource able to dispatch presses to bound handlers.
 */
export function createTestKeyboardSource() {
    const handlers = new Map();
    const emit = (type, event) => {
        for (const handler of handlers.get(type) ?? []) {
            handler(event);
        }
        return event;
    };
    return {
        addKeyListener: (type, handler) => {
            const existing = handlers.get(type) ?? [];
            existing.push(handler);
            handlers.set(type, existing);
        },
        press: (key, repeat = false) => emit("keydown", new KeyboardEvent("keydown", { key, repeat, cancelable: true })),
        release: (key) => emit("keyup", new KeyboardEvent("keyup", { key, cancelable: true })),
        boundCount: (type) => (handlers.get(type) ?? []).length,
    };
}
/**
 * Create a touch event source over plain touch points.
 *
 * Returns:
 *     TestTouchSource able to dispatch points to bound handlers.
 */
export function createTestTouchSource() {
    const handlers = new Map();
    const passive = new Map();
    let clock = 0;
    return {
        addTouchListener: (type, handler, isPassive) => {
            const existing = handlers.get(type) ?? [];
            existing.push(handler);
            handlers.set(type, existing);
            passive.set(type, isPassive);
        },
        now: () => clock,
        emit: (type, points) => {
            let consumed = false;
            for (const handler of handlers.get(type) ?? []) {
                if (handler(points)) {
                    consumed = true;
                }
            }
            return consumed;
        },
        setNow: (value) => {
            clock = value;
        },
        passiveFor: (type) => passive.get(type),
    };
}
//# sourceMappingURL=fixtures.js.map