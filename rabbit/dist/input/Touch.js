/**
 * Touch input source - dynamic invisible joystick.
 *
 * A joystick anchors wherever the touch starts and translates drag direction
 * into 8-way movement; a quick tap requests a jump. Like the keyboard, this
 * source only produces intent and submits it to the arbiter.
 */
import { NEUTRAL_INTENT, createIntent, } from "./intent.js";
/** Default touch configuration. */
export const DEFAULT_TOUCH_CONFIG = {
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
export function createTouchState() {
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
export function calculateDirection(joystick, config) {
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
    }
    else if (degrees >= 22.5 && degrees < 67.5) {
        return "up-right";
    }
    else if (degrees >= 67.5 && degrees < 112.5) {
        return "up";
    }
    else if (degrees >= 112.5 && degrees < 157.5) {
        return "up-left";
    }
    else if (degrees >= 157.5 && degrees < 202.5) {
        return "left";
    }
    else if (degrees >= 202.5 && degrees < 247.5) {
        return "down-left";
    }
    else if (degrees >= 247.5 && degrees < 292.5) {
        return "down";
    }
    else {
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
function directionToHorizontal(direction) {
    if (direction === null)
        return null;
    if (direction.includes("left"))
        return "left";
    if (direction.includes("right"))
        return "right";
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
function directionToVertical(direction) {
    if (direction === null)
        return null;
    if (direction.includes("up"))
        return "up";
    if (direction.includes("down"))
        return "down";
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
export function directionToIntent(direction) {
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
export function isTap(joystick, releaseTime, config) {
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
export function processDirectionChange(newDirection, touchState, deps) {
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
export function handleTouchEnd(touchState, deps, releaseTime) {
    const joystick = touchState.joystick;
    if (joystick === null)
        return;
    deps.activity.record();
    if (isTap(joystick, releaseTime, deps.config)) {
        deps.arbiter.requestJump("user");
    }
    else {
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
function findTouchByIdentifier(points, identifier) {
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
export function handleTouchStart(touchState, points, now) {
    if (touchState.joystick !== null)
        return false;
    const touch = points[0];
    if (touch === undefined)
        return false;
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
export function handleTouchMove(touchState, deps, points) {
    const joystick = touchState.joystick;
    if (joystick === null)
        return false;
    const touch = findTouchByIdentifier(points, joystick.identifier);
    if (touch === undefined)
        return false;
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
export function handleTouchEndEvent(touchState, deps, points, now) {
    const joystick = touchState.joystick;
    if (joystick === null)
        return;
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
export function setupTouchControls(deps) {
    const touchState = createTouchState();
    deps.events.addTouchListener("touchstart", (points) => {
        handleTouchStart(touchState, points, deps.events.now());
        return false;
    }, true);
    deps.events.addTouchListener("touchmove", (points) => handleTouchMove(touchState, deps, points), false);
    const onEnd = (points) => {
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
//# sourceMappingURL=Touch.js.map