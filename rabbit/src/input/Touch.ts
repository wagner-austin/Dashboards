/**
 * Touch input source - dynamic invisible joystick.
 *
 * A joystick anchors wherever the touch starts and translates drag direction
 * into 8-way movement; a quick tap requests a jump. Like the keyboard, this
 * source only produces intent and submits it to the arbiter.
 */

import type { ActivityTracker } from "./activity.js";
import type { InputArbiter } from "./arbiter.js";
import {
  NEUTRAL_INTENT,
  createIntent,
  type HorizontalInput,
  type MovementIntent,
  type VerticalInput,
} from "./intent.js";

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
export type TouchDirection =
  | "up"
  | "down"
  | "left"
  | "right"
  | "up-left"
  | "up-right"
  | "down-left"
  | "down-right"
  | null;

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
  readonly addTouchListener: (
    type: TouchEventType,
    handler: (points: readonly TouchPoint[]) => boolean,
    passive: boolean
  ) => void;
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
export const DEFAULT_TOUCH_CONFIG: TouchConfig = {
  deadzone: 20,
  tapThreshold: 200,
  tapMaxDistance: 15,
};

/**
 * Create initial touch state.
 *
 * Returns:
 *     TouchState with no active joystick.
 */
export function createTouchState(): TouchState {
  return {
    joystick: null,
    currentDirection: null,
  };
}

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
export function calculateDirection(
  joystick: JoystickState,
  config: TouchConfig
): TouchDirection {
  const dx = joystick.currentX - joystick.anchorX;
  const dy = joystick.currentY - joystick.anchorY;
  const distance = Math.sqrt(dx * dx + dy * dy);

  if (distance < config.deadzone) {
    return null;
  }

  // Angle in radians, 0 = right, counter-clockwise.
  // Negate dy because screen Y is inverted (down is positive).
  const angle = Math.atan2(-dy, dx);
  const degrees = ((angle * 180) / Math.PI + 360) % 360;

  if (degrees >= 337.5 || degrees < 22.5) {
    return "right";
  } else if (degrees >= 22.5 && degrees < 67.5) {
    return "up-right";
  } else if (degrees >= 67.5 && degrees < 112.5) {
    return "up";
  } else if (degrees >= 112.5 && degrees < 157.5) {
    return "up-left";
  } else if (degrees >= 157.5 && degrees < 202.5) {
    return "left";
  } else if (degrees >= 202.5 && degrees < 247.5) {
    return "down-left";
  } else if (degrees >= 247.5 && degrees < 292.5) {
    return "down";
  } else {
    return "down-right";
  }
}

/**
 * Extract the horizontal component of a touch direction.
 *
 * Args:
 *     direction: Touch direction to decompose.
 *
 * Returns:
 *     The horizontal component, or null.
 */
function directionToHorizontal(direction: TouchDirection): HorizontalInput {
  if (direction === null) return null;
  if (direction.includes("left")) return "left";
  if (direction.includes("right")) return "right";
  return null;
}

/**
 * Extract the vertical component of a touch direction.
 *
 * Args:
 *     direction: Touch direction to decompose.
 *
 * Returns:
 *     The vertical component, or null.
 */
function directionToVertical(direction: TouchDirection): VerticalInput {
  if (direction === null) return null;
  if (direction.includes("up")) return "up";
  if (direction.includes("down")) return "down";
  return null;
}

/**
 * Convert a touch direction into a movement intent.
 *
 * Args:
 *     direction: Touch direction to convert.
 *
 * Returns:
 *     The intent that direction requests.
 */
export function directionToIntent(direction: TouchDirection): MovementIntent {
  return createIntent(directionToHorizontal(direction), directionToVertical(direction));
}

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
export function isTap(
  joystick: JoystickState,
  releaseTime: number,
  config: TouchConfig
): boolean {
  const duration = releaseTime - joystick.startTime;
  const dx = joystick.currentX - joystick.anchorX;
  const dy = joystick.currentY - joystick.anchorY;
  const distance = Math.sqrt(dx * dx + dy * dy);

  return duration < config.tapThreshold && distance < config.tapMaxDistance;
}

/**
 * Submit the intent for a new joystick direction.
 *
 * Args:
 *     newDirection: Direction the joystick now points.
 *     touchState: Touch state to update.
 *     deps: Touch dependencies.
 */
export function processDirectionChange(
  newDirection: TouchDirection,
  touchState: TouchState,
  deps: TouchDeps
): void {
  deps.activity.record();
  deps.arbiter.submit("user", directionToIntent(newDirection));
  touchState.currentDirection = newDirection;
}

/**
 * Handle a completed touch: jump on a tap, otherwise release all input.
 *
 * Args:
 *     touchState: Touch state to update.
 *     deps: Touch dependencies.
 *     releaseTime: Time of release, in milliseconds.
 */
export function handleTouchEnd(
  touchState: TouchState,
  deps: TouchDeps,
  releaseTime: number
): void {
  const joystick = touchState.joystick;
  if (joystick === null) return;

  deps.activity.record();

  if (isTap(joystick, releaseTime, deps.config)) {
    deps.arbiter.requestJump("user");
  } else {
    deps.arbiter.submit("user", NEUTRAL_INTENT);
  }

  touchState.joystick = null;
  touchState.currentDirection = null;
}

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
function findTouchByIdentifier(
  points: readonly TouchPoint[],
  identifier: number
): TouchPoint | undefined {
  for (const point of points) {
    if (point.identifier === identifier) {
      return point;
    }
  }
  return undefined;
}

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
export function handleTouchStart(
  touchState: TouchState,
  points: readonly TouchPoint[],
  now: number
): boolean {
  if (touchState.joystick !== null) return false;

  const touch = points[0];
  if (touch === undefined) return false;

  touchState.joystick = {
    anchorX: touch.clientX,
    anchorY: touch.clientY,
    currentX: touch.clientX,
    currentY: touch.clientY,
    startTime: now,
    identifier: touch.identifier,
  };

  return true;
}

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
export function handleTouchMove(
  touchState: TouchState,
  deps: TouchDeps,
  points: readonly TouchPoint[]
): boolean {
  const joystick = touchState.joystick;
  if (joystick === null) return false;

  const touch = findTouchByIdentifier(points, joystick.identifier);
  if (touch === undefined) return false;

  joystick.currentX = touch.clientX;
  joystick.currentY = touch.clientY;

  const newDirection = calculateDirection(joystick, deps.config);

  if (newDirection !== touchState.currentDirection) {
    processDirectionChange(newDirection, touchState, deps);
  }

  return true;
}

/**
 * Handle touchend or touchcancel, ending the gesture when our touch is gone.
 *
 * Args:
 *     touchState: Touch state to update.
 *     deps: Touch dependencies.
 *     points: Remaining active touch points from the event.
 *     now: Current timestamp in milliseconds.
 */
export function handleTouchEndEvent(
  touchState: TouchState,
  deps: TouchDeps,
  points: readonly TouchPoint[],
  now: number
): void {
  const joystick = touchState.joystick;
  if (joystick === null) return;

  if (findTouchByIdentifier(points, joystick.identifier) === undefined) {
    handleTouchEnd(touchState, deps, now);
  }
}

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
export function setupTouchControls(deps: TouchDeps): TouchState {
  const touchState = createTouchState();

  deps.events.addTouchListener(
    "touchstart",
    (points: readonly TouchPoint[]): boolean => {
      handleTouchStart(touchState, points, deps.events.now());
      return false;
    },
    true
  );

  deps.events.addTouchListener(
    "touchmove",
    (points: readonly TouchPoint[]): boolean => handleTouchMove(touchState, deps, points),
    false
  );

  const onEnd = (points: readonly TouchPoint[]): boolean => {
    handleTouchEndEvent(touchState, deps, points, deps.events.now());
    return false;
  };

  deps.events.addTouchListener("touchend", onEnd, true);
  deps.events.addTouchListener("touchcancel", onEnd, true);

  return touchState;
}

/** Test hooks for internal functions. */
export const _test_hooks = {
  createTouchState,
  calculateDirection,
  isTap,
  directionToHorizontal,
  directionToVertical,
  directionToIntent,
  processDirectionChange,
  handleTouchEnd,
  handleTouchStart,
  handleTouchMove,
  handleTouchEndEvent,
  findTouchByIdentifier,
  setupTouchControls,
  DEFAULT_TOUCH_CONFIG,
};
