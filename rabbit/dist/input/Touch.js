/**
 * Touch input handling with dynamic invisible joystick.
 *
 * Implements a virtual joystick that anchors at the touch point and
 * translates drag direction into 8-way movement input. Tap gestures
 * trigger jump. Uses the unified input model shared with keyboard.
 */
import { isHopping, isJumping, } from "../entities/Bunny.js";
import { processInputChange, } from "./Keyboard.js";
import { isPendingJump, handleJumpInput, } from "./handlers.js";
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
export function calculateDirection(joystick, config) {
    const dx = joystick.currentX - joystick.anchorX;
    const dy = joystick.currentY - joystick.anchorY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    if (distance < config.deadzone) {
        return null;
    }
    // Angle in radians, 0 = right, counter-clockwise
    // Negate dy because screen Y is inverted (down is positive)
    const angle = Math.atan2(-dy, dx);
    // Convert angle to degrees for easier sector calculation
    // Normalize to 0-360 range
    const degrees = ((angle * 180) / Math.PI + 360) % 360;
    // Map to 8 directions using 45-degree sectors
    // Each direction has a 45-degree range centered on it
    // Right: 337.5-22.5, Up-Right: 22.5-67.5, Up: 67.5-112.5, etc.
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
 * Extract horizontal component from touch direction.
 *
 * Args:
 *     direction: Touch direction to extract from.
 *
 * Returns:
 *     HorizontalInput extracted from direction.
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
 * Extract vertical component from touch direction.
 *
 * Args:
 *     direction: Touch direction to extract from.
 *
 * Returns:
 *     VerticalInput extracted from direction.
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
export function isTap(joystick, releaseTime, config) {
    const duration = releaseTime - joystick.startTime;
    const dx = joystick.currentX - joystick.anchorX;
    const dy = joystick.currentY - joystick.anchorY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    return duration < config.tapThreshold && distance < config.tapMaxDistance;
}
/**
 * Process a new direction and update input state.
 *
 * Converts touch direction to horizontal/vertical components and
 * calls the shared processInputChange function.
 *
 * Args:
 *     prevDirection: Previous touch direction.
 *     newDirection: New touch direction.
 *     touchState: Touch state to update.
 *     inputState: Game input state to update.
 *     bunnyFrames: Bunny animation frames.
 *     bunnyTimers: Bunny animation timers.
 */
export function processDirectionChange(prevDirection, newDirection, touchState, inputState, bunnyFrames, bunnyTimers) {
    const prevHorizontal = directionToHorizontal(prevDirection);
    const prevVertical = directionToVertical(prevDirection);
    const newHorizontal = directionToHorizontal(newDirection);
    const newVertical = directionToVertical(newDirection);
    // Update raw input state
    inputState.horizontalHeld = newHorizontal;
    inputState.verticalHeld = newVertical;
    // Use shared input change processor
    processInputChange(prevHorizontal, prevVertical, newHorizontal, newVertical, inputState, bunnyFrames, bunnyTimers);
    touchState.currentDirection = newDirection;
}
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
export function handleTouchEnd(touchState, inputState, bunnyFrames, bunnyTimers, releaseTime, config) {
    if (touchState.joystick === null)
        return;
    // Check for tap (jump)
    if (isTap(touchState.joystick, releaseTime, config)) {
        if (!isJumping(inputState.bunny) && !isPendingJump(inputState.bunny) && !isHopping(inputState.bunny)) {
            handleJumpInput(inputState.bunny, bunnyFrames, bunnyTimers);
        }
    }
    else {
        // Regular release - end all inputs via processInputChange
        const prevHorizontal = inputState.horizontalHeld;
        const prevVertical = inputState.verticalHeld;
        inputState.horizontalHeld = null;
        inputState.verticalHeld = null;
        processInputChange(prevHorizontal, prevVertical, null, null, inputState, bunnyFrames, bunnyTimers);
    }
    touchState.joystick = null;
    touchState.currentDirection = null;
}
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
function findTouchByIdentifier(touches, identifier) {
    for (const touch of touches) {
        if (touch.identifier === identifier) {
            return touch;
        }
    }
    return undefined;
}
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
function hasTouchWithIdentifier(touches, identifier) {
    return findTouchByIdentifier(touches, identifier) !== undefined;
}
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
export function handleTouchStart(touchState, touches, now) {
    if (touchState.joystick !== null)
        return false;
    const touch = touches[0];
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
export function handleTouchMove(touchState, inputState, bunnyFrames, bunnyTimers, touches, config) {
    if (touchState.joystick === null)
        return false;
    const touch = findTouchByIdentifier(touches, touchState.joystick.identifier);
    if (touch === undefined)
        return false;
    const prevDirection = touchState.currentDirection;
    touchState.joystick.currentX = touch.clientX;
    touchState.joystick.currentY = touch.clientY;
    const newDirection = calculateDirection(touchState.joystick, config);
    if (newDirection !== prevDirection) {
        processDirectionChange(prevDirection, newDirection, touchState, inputState, bunnyFrames, bunnyTimers);
    }
    return true;
}
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
export function handleTouchEndEvent(touchState, inputState, bunnyFrames, bunnyTimers, touches, now, config) {
    if (touchState.joystick === null)
        return;
    const stillActive = hasTouchWithIdentifier(touches, touchState.joystick.identifier);
    if (!stillActive) {
        handleTouchEnd(touchState, inputState, bunnyFrames, bunnyTimers, now, config);
    }
}
/**
 * Setup touch controls for the game.
 *
 * Attaches touch event listeners to the document and translates
 * touch gestures into input state changes using the shared input model.
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
export function setupTouchControls(inputState, bunnyFrames, bunnyTimers, config = DEFAULT_TOUCH_CONFIG) {
    const touchState = createTouchState();
    document.addEventListener("touchstart", (e) => {
        handleTouchStart(touchState, e.touches, Date.now());
        // Note: Do NOT call preventDefault() here - it blocks audio autoplay on mobile
    });
    document.addEventListener("touchmove", (e) => {
        if (handleTouchMove(touchState, inputState, bunnyFrames, bunnyTimers, e.touches, config)) {
            e.preventDefault();
        }
    }, { passive: false });
    const onEnd = (e) => {
        handleTouchEndEvent(touchState, inputState, bunnyFrames, bunnyTimers, e.touches, Date.now(), config);
    };
    document.addEventListener("touchend", onEnd);
    document.addEventListener("touchcancel", onEnd);
    return touchState;
}
/** Test hooks for internal functions. */
export const _test_hooks = {
    createTouchState,
    calculateDirection,
    isTap,
    processDirectionChange,
    handleTouchEnd,
    handleTouchStart,
    handleTouchMove,
    handleTouchEndEvent,
    directionToHorizontal,
    directionToVertical,
    findTouchByIdentifier,
    hasTouchWithIdentifier,
    DEFAULT_TOUCH_CONFIG,
};
//# sourceMappingURL=Touch.js.map