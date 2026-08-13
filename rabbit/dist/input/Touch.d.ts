/**
 * Touch input source - dynamic invisible joystick.
 *
 * A joystick anchors wherever the touch starts and translates drag direction
 * into 8-way movement; a quick tap requests a jump. Like the keyboard, this
 * source only produces intent and submits it to the arbiter.
 */
import type { ActivityTracker } from "./activity.js";
import type { InputArbiter } from "./arbiter.js";
import { type HorizontalInput, type MovementIntent, type VerticalInput } from "./intent.js";
/**
 * Touch joystick state tracking.
 *
 * anchorX: X coordinate where the touch started (joystick center).
 * anchorY: Y coordinate where the touch started (joystick center).
 * currentX: Current touch X position.
 * currentY: Current touch Y position.
 * startTime: When the touch started, for tap detection.
 * identifier: Touch.identifier for multi-touch tracking.
 */
export interface JoystickState {
    readonly anchorX: number;
    readonly anchorY: number;
    currentX: number;
    currentY: number;
    readonly startTime: number;
    readonly identifier: number;
}
/**
 * Touch input state.
 *
 * joystick: Active joystick, or null when no touch is down.
 * currentDirection: Direction derived from the joystick angle.
 */
export interface TouchState {
    joystick: JoystickState | null;
    currentDirection: TouchDirection;
}
/**
 * Direction calculated from the touch joystick angle.
 *
 * The 8 cardinal and diagonal directions, plus null for the deadzone.
 */
export type TouchDirection = "up" | "down" | "left" | "right" | "up-left" | "up-right" | "down-left" | "down-right" | null;
/**
 * Configuration for touch behaviour.
 *
 * deadzone: Minimum drag distance to register a direction, in pixels.
 * tapThreshold: Maximum duration for tap detection, in milliseconds.
 * tapMaxDistance: Maximum movement for tap detection, in pixels.
 */
export interface TouchConfig {
    readonly deadzone: number;
    readonly tapThreshold: number;
    readonly tapMaxDistance: number;
}
/** Touch event types this source binds to. */
export type TouchEventType = "touchstart" | "touchmove" | "touchend" | "touchcancel";
/**
 * The only properties of a DOM Touch this module needs.
 *
 * Depending on this rather than on Touch/TouchList keeps the joystick free of
 * the DOM: the adapter parses browser events at the edge, and everything
 * downstream works on plain values.
 *
 * identifier: Stable id used to follow one finger across events.
 * clientX: Horizontal position in viewport pixels.
 * clientY: Vertical position in viewport pixels.
 */
export interface TouchPoint {
    readonly identifier: number;
    readonly clientX: number;
    readonly clientY: number;
}
/**
 * Minimal interface over the event target the joystick binds to.
 *
 * A handler returns true when it has consumed the gesture, which the adapter
 * turns into preventDefault. `now` is injected rather than read from the clock
 * so tap detection is exercised with exact timestamps.
 */
export interface TouchEventSource {
    readonly addTouchListener: (type: TouchEventType, handler: (points: readonly TouchPoint[]) => boolean, passive: boolean) => void;
    readonly now: () => number;
}
/**
 * Dependencies required to run the touch source.
 *
 * arbiter: Receives this source's intent and jump requests.
 * activity: Idle timer reset on every touch.
 * events: Event target to bind listeners to.
 * config: Joystick tuning values.
 */
export interface TouchDeps {
    readonly arbiter: InputArbiter;
    readonly activity: ActivityTracker;
    readonly events: TouchEventSource;
    readonly config: TouchConfig;
}
/** Default touch configuration. */
export declare const DEFAULT_TOUCH_CONFIG: TouchConfig;
/**
 * Create initial touch state.
 *
 * Returns:
 *     TouchState with no active joystick.
 */
export declare function createTouchState(): TouchState;
/**
 * Calculate direction from the joystick anchor to the current touch position.
 *
 * Uses 45-degree sectors centred on each of the 8 directions, with a deadzone
 * around the anchor.
 *
 * Args:
 *     joystick: Current joystick state.
 *     config: Touch configuration.
 *
 * Returns:
 *     TouchDirection, or null when inside the deadzone.
 */
export declare function calculateDirection(joystick: JoystickState, config: TouchConfig): TouchDirection;
/**
 * Extract the horizontal component of a touch direction.
 *
 * Args:
 *     direction: Touch direction to decompose.
 *
 * Returns:
 *     The horizontal component, or null.
 */
declare function directionToHorizontal(direction: TouchDirection): HorizontalInput;
/**
 * Extract the vertical component of a touch direction.
 *
 * Args:
 *     direction: Touch direction to decompose.
 *
 * Returns:
 *     The vertical component, or null.
 */
declare function directionToVertical(direction: TouchDirection): VerticalInput;
/**
 * Convert a touch direction into a movement intent.
 *
 * Args:
 *     direction: Touch direction to convert.
 *
 * Returns:
 *     The intent that direction requests.
 */
export declare function directionToIntent(direction: TouchDirection): MovementIntent;
/**
 * Check whether a touch qualifies as a tap.
 *
 * Args:
 *     joystick: Joystick state at release.
 *     releaseTime: Time of release, in milliseconds.
 *     config: Touch configuration.
 *
 * Returns:
 *     True if the touch was short and barely moved.
 */
export declare function isTap(joystick: JoystickState, releaseTime: number, config: TouchConfig): boolean;
/**
 * Submit the intent for a new joystick direction.
 *
 * Args:
 *     newDirection: Direction the joystick now points.
 *     touchState: Touch state to update.
 *     deps: Touch dependencies.
 */
export declare function processDirectionChange(newDirection: TouchDirection, touchState: TouchState, deps: TouchDeps): void;
/**
 * Handle a completed touch: jump on a tap, otherwise release all input.
 *
 * Args:
 *     touchState: Touch state to update.
 *     deps: Touch dependencies.
 *     releaseTime: Time of release, in milliseconds.
 */
export declare function handleTouchEnd(touchState: TouchState, deps: TouchDeps, releaseTime: number): void;
/**
 * Find a touch point by identifier.
 *
 * Args:
 *     points: Active touch points.
 *     identifier: Touch identifier to find.
 *
 * Returns:
 *     The matching point, or undefined.
 */
declare function findTouchByIdentifier(points: readonly TouchPoint[], identifier: number): TouchPoint | undefined;
/**
 * Handle a touchstart event by anchoring a joystick.
 *
 * Args:
 *     touchState: Touch state to update.
 *     points: Active touch points from the event.
 *     now: Current timestamp in milliseconds.
 *
 * Returns:
 *     True if a joystick was created.
 */
export declare function handleTouchStart(touchState: TouchState, points: readonly TouchPoint[], now: number): boolean;
/**
 * Handle a touchmove event by re-aiming the joystick.
 *
 * Args:
 *     touchState: Touch state to update.
 *     deps: Touch dependencies.
 *     points: Active touch points from the event.
 *
 * Returns:
 *     True if the tracked touch was handled.
 */
export declare function handleTouchMove(touchState: TouchState, deps: TouchDeps, points: readonly TouchPoint[]): boolean;
/**
 * Handle touchend or touchcancel, ending the gesture when our touch is gone.
 *
 * Args:
 *     touchState: Touch state to update.
 *     deps: Touch dependencies.
 *     points: Remaining active touch points from the event.
 *     now: Current timestamp in milliseconds.
 */
export declare function handleTouchEndEvent(touchState: TouchState, deps: TouchDeps, points: readonly TouchPoint[], now: number): void;
/**
 * Bind touch listeners and start producing intent.
 *
 * touchstart is deliberately not prevented: preventing it blocks audio
 * autoplay unlocking on mobile.
 *
 * Args:
 *     deps: Touch dependencies.
 *
 * Returns:
 *     The joystick state this source maintains.
 */
export declare function setupTouchControls(deps: TouchDeps): TouchState;
/** Test hooks for internal functions. */
export declare const _test_hooks: {
    createTouchState: typeof createTouchState;
    calculateDirection: typeof calculateDirection;
    isTap: typeof isTap;
    directionToHorizontal: typeof directionToHorizontal;
    directionToVertical: typeof directionToVertical;
    directionToIntent: typeof directionToIntent;
    processDirectionChange: typeof processDirectionChange;
    handleTouchEnd: typeof handleTouchEnd;
    handleTouchStart: typeof handleTouchStart;
    handleTouchMove: typeof handleTouchMove;
    handleTouchEndEvent: typeof handleTouchEndEvent;
    findTouchByIdentifier: typeof findTouchByIdentifier;
    setupTouchControls: typeof setupTouchControls;
    DEFAULT_TOUCH_CONFIG: TouchConfig;
};
export {};
//# sourceMappingURL=Touch.d.ts.map