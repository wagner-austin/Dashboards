/**
 * Touch input handling with dynamic invisible joystick.
 *
 * Implements a virtual joystick that anchors at the touch point and
 * translates drag direction into 8-way movement input. Tap gestures
 * trigger jump. Uses the same shared handlers as keyboard input.
 */
import { type BunnyFrames, type BunnyTimers } from "../entities/Bunny.js";
import type { InputState } from "./Keyboard.js";
/**
 * Touch joystick state tracking.
 *
 * anchorX, anchorY: Where the touch started (joystick center).
 * currentX, currentY: Current touch position.
 * startTime: When touch started (for tap detection).
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
 * joystick: Active joystick or null if no touch.
 * currentDirection: Current direction derived from joystick angle.
 */
export interface TouchState {
    joystick: JoystickState | null;
    currentDirection: TouchDirection;
}
/**
 * Direction calculated from touch joystick angle.
 *
 * Represents the 8 cardinal + diagonal directions plus null (no movement/deadzone).
 */
export type TouchDirection = "up" | "down" | "left" | "right" | "up-left" | "up-right" | "down-left" | "down-right" | null;
/**
 * Configuration for touch behavior.
 *
 * deadzone: Minimum drag distance to register as direction (pixels).
 * tapThreshold: Maximum time for tap detection (milliseconds).
 * tapMaxDistance: Maximum movement for tap detection (pixels).
 */
export interface TouchConfig {
    readonly deadzone: number;
    readonly tapThreshold: number;
    readonly tapMaxDistance: number;
}
/** Default touch configuration */
export declare const DEFAULT_TOUCH_CONFIG: TouchConfig;
/**
 * Create initial touch state.
 *
 * Returns:
 *     TouchState with no active joystick.
 */
export declare function createTouchState(): TouchState;
/**
 * Calculate direction from anchor to current touch position.
 *
 * Uses 8-direction calculation with deadzone. Returns null if within deadzone.
 * Directions are mapped using 45-degree sectors centered on each direction.
 *
 * Args:
 *     joystick: Current joystick state.
 *     config: Touch configuration.
 *
 * Returns:
 *     TouchDirection or null if within deadzone.
 */
export declare function calculateDirection(joystick: JoystickState, config: TouchConfig): TouchDirection;
/**
 * Check if direction is up (includes "up" but not just up-left/up-right without up).
 *
 * Args:
 *     direction: Touch direction to check.
 *
 * Returns:
 *     True if direction includes up.
 */
declare function isUp(direction: TouchDirection): boolean;
/**
 * Check if direction is down (includes "down").
 *
 * Args:
 *     direction: Touch direction to check.
 *
 * Returns:
 *     True if direction includes down.
 */
declare function isDown(direction: TouchDirection): boolean;
/**
 * Check if direction is left (includes "left").
 *
 * Args:
 *     direction: Touch direction to check.
 *
 * Returns:
 *     True if direction includes left.
 */
declare function isLeft(direction: TouchDirection): boolean;
/**
 * Check if direction is right (includes "right").
 *
 * Args:
 *     direction: Touch direction to check.
 *
 * Returns:
 *     True if direction includes right.
 */
declare function isRight(direction: TouchDirection): boolean;
/**
 * Check if a touch qualifies as a tap (quick touch-release).
 *
 * Args:
 *     joystick: Joystick state at release.
 *     releaseTime: Time of release (ms since epoch).
 *     config: Touch configuration.
 *
 * Returns:
 *     True if touch qualifies as a tap.
 */
export declare function isTap(joystick: JoystickState, releaseTime: number, config: TouchConfig): boolean;
/**
 * Process a new direction and generate appropriate input actions.
 *
 * Compares previous direction to new direction and triggers
 * the appropriate start/end handlers for movement.
 *
 * Args:
 *     prevDirection: Previous touch direction.
 *     newDirection: New touch direction.
 *     touchState: Touch state to update.
 *     inputState: Game input state to update.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 */
export declare function processDirectionChange(prevDirection: TouchDirection, newDirection: TouchDirection, touchState: TouchState, inputState: InputState, bunnyFrames: BunnyFrames, bunnyTimers: BunnyTimers): void;
/**
 * Handle touch release - end all inputs or trigger jump on tap.
 *
 * Args:
 *     touchState: Touch state to update.
 *     inputState: Game input state to update.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 *     releaseTime: Time of release (ms since epoch).
 *     config: Touch configuration.
 */
export declare function handleTouchEnd(touchState: TouchState, inputState: InputState, bunnyFrames: BunnyFrames, bunnyTimers: BunnyTimers, releaseTime: number, config: TouchConfig): void;
/**
 * Find a touch by identifier in a TouchList.
 *
 * Args:
 *     touches: TouchList to search.
 *     identifier: Touch identifier to find.
 *
 * Returns:
 *     Touch if found, undefined otherwise.
 */
declare function findTouchByIdentifier(touches: TouchList, identifier: number): Touch | undefined;
/**
 * Check if a touch with given identifier exists in a TouchList.
 *
 * Args:
 *     touches: TouchList to search.
 *     identifier: Touch identifier to find.
 *
 * Returns:
 *     True if touch with identifier exists.
 */
declare function hasTouchWithIdentifier(touches: TouchList, identifier: number): boolean;
/**
 * Handle touchstart event.
 *
 * Creates a new joystick at the touch point if none exists.
 *
 * Args:
 *     touchState: Touch state to update.
 *     touches: TouchList from the event.
 *     now: Current timestamp in milliseconds.
 *
 * Returns:
 *     True if a joystick was created (event should be prevented).
 */
export declare function handleTouchStart(touchState: TouchState, touches: TouchList, now: number): boolean;
/**
 * Handle touchmove event.
 *
 * Updates joystick position and triggers direction changes.
 *
 * Args:
 *     touchState: Touch state to update.
 *     inputState: Game input state.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 *     touches: TouchList from the event.
 *     config: Touch configuration.
 *
 * Returns:
 *     True if the touch was handled (event should be prevented).
 */
export declare function handleTouchMove(touchState: TouchState, inputState: InputState, bunnyFrames: BunnyFrames, bunnyTimers: BunnyTimers, touches: TouchList, config: TouchConfig): boolean;
/**
 * Handle touchend or touchcancel event.
 *
 * Ends the touch interaction if our tracked touch is no longer active.
 *
 * Args:
 *     touchState: Touch state to update.
 *     inputState: Game input state.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 *     touches: TouchList from the event (remaining active touches).
 *     now: Current timestamp in milliseconds.
 *     config: Touch configuration.
 */
export declare function handleTouchEndEvent(touchState: TouchState, inputState: InputState, bunnyFrames: BunnyFrames, bunnyTimers: BunnyTimers, touches: TouchList, now: number, config: TouchConfig): void;
/**
 * Setup touch controls for the game.
 *
 * Attaches touch event listeners to the document and translates
 * touch gestures into input actions using the shared handlers.
 *
 * Args:
 *     inputState: Game input state.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 *     config: Touch configuration (optional, uses defaults).
 *
 * Returns:
 *     TouchState for external access if needed.
 */
export declare function setupTouchControls(inputState: InputState, bunnyFrames: BunnyFrames, bunnyTimers: BunnyTimers, config?: TouchConfig): TouchState;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createTouchState: typeof createTouchState;
    calculateDirection: typeof calculateDirection;
    isTap: typeof isTap;
    processDirectionChange: typeof processDirectionChange;
    handleTouchEnd: typeof handleTouchEnd;
    handleTouchStart: typeof handleTouchStart;
    handleTouchMove: typeof handleTouchMove;
    handleTouchEndEvent: typeof handleTouchEndEvent;
    isUp: typeof isUp;
    isDown: typeof isDown;
    isLeft: typeof isLeft;
    isRight: typeof isRight;
    findTouchByIdentifier: typeof findTouchByIdentifier;
    hasTouchWithIdentifier: typeof hasTouchWithIdentifier;
    DEFAULT_TOUCH_CONFIG: TouchConfig;
};
export {};
//# sourceMappingURL=Touch.d.ts.map