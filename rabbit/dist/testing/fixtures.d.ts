/**
 * Shared test fixtures for the input layer.
 *
 * These are real implementations, not stand-ins: the frame data is real frame
 * data, the event sources really store and replay handlers, and the draw
 * source really returns the sequence it was given. Nothing here fakes the
 * behaviour under test - it only supplies inputs that would otherwise be
 * duplicated across every suite.
 */
import { type AnimationState, type BunnyFrames, type BunnyState, type BunnyTimers } from "../entities/Bunny.js";
import type { RandomSource } from "../input/Autopilot.js";
import type { KeyEventType, KeyboardEventSource } from "../input/Keyboard.js";
import { type InputState } from "../input/state.js";
import type { TouchEventSource, TouchEventType, TouchPoint } from "../input/Touch.js";
import { type DepthBounds } from "../world/Projection.js";
/**
 * Create bunny frames with distinguishable labels per animation.
 *
 * Returns:
 *     BunnyFrames whose entries identify the animation and index they came from.
 */
export declare function createTestFrames(): BunnyFrames;
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
export declare function createTestBunnyState(animation: AnimationState, facingRight?: boolean): BunnyState;
/**
 * Create depth bounds matching the shipped layer range of 8 to 30.
 *
 * Returns:
 *     DepthBounds derived from the real projection maths.
 */
export declare function createTestDepthBounds(): DepthBounds;
/**
 * Create input state around a bunny, with a neutral intent.
 *
 * Args:
 *     bunny: Bunny state to wrap.
 *
 * Returns:
 *     InputState positioned at the origin.
 */
export declare function createTestInputState(bunny: BunnyState): InputState;
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
export declare function createTestTimers(bunny: BunnyState, frames: BunnyFrames, isHorizontalHeld: () => boolean): BunnyTimers;
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
export declare function createSequenceRandom(draws: readonly number[]): RandomSource;
/**
 * Create a draw source that always returns the same value.
 *
 * Args:
 *     value: Value to return for every draw.
 *
 * Returns:
 *     RandomSource returning that value.
 */
export declare function createConstantRandom(value: number): RandomSource;
/** Keyboard event source that replays presses to the bound handlers. */
export interface TestKeyboardSource extends KeyboardEventSource {
    /** Dispatch a keydown and return the event, for asserting preventDefault. */
    readonly press: (key: string, repeat?: boolean) => KeyboardEvent;
    /** Dispatch a keyup and return the event. */
    readonly release: (key: string) => KeyboardEvent;
    /** Number of handlers bound per event type. */
    readonly boundCount: (type: KeyEventType) => number;
}
/**
 * Create a keyboard event source backed by real KeyboardEvent objects.
 *
 * Returns:
 *     TestKeyboardSource able to dispatch presses to bound handlers.
 */
export declare function createTestKeyboardSource(): TestKeyboardSource;
/** Touch event source that replays touch points to the bound handlers. */
export interface TestTouchSource extends TouchEventSource {
    /** Dispatch touch points and return whether a handler consumed them. */
    readonly emit: (type: TouchEventType, points: readonly TouchPoint[]) => boolean;
    /** Set the timestamp returned by `now`. */
    readonly setNow: (value: number) => void;
    /** Passive flag recorded for a bound event type. */
    readonly passiveFor: (type: TouchEventType) => boolean | undefined;
}
/**
 * Create a touch event source over plain touch points.
 *
 * Returns:
 *     TestTouchSource able to dispatch points to bound handlers.
 */
export declare function createTestTouchSource(): TestTouchSource;
//# sourceMappingURL=fixtures.d.ts.map