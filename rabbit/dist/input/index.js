/**
 * Input module public API.
 *
 * Re-exports keyboard and touch controls for external use.
 */
export { setupKeyboardControls, processDepthMovement, processHorizontalMovement, processWalkMovement, } from "./Keyboard.js";
export { setupTouchControls, createTouchState, calculateDirection, isTap, processDirectionChange, handleTouchEnd, DEFAULT_TOUCH_CONFIG, } from "./Touch.js";
export { isPendingJump, handleJumpInput, handleWalkKeyDown, handleWalkKeyUp, handleHopInput, handleHopRelease, } from "./handlers.js";
//# sourceMappingURL=index.js.map