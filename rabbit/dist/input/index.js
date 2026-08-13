/**
 * Input module public API.
 *
 * The layer is assembled by `createInputSystem`; the individual services are
 * exported for tests and for callers that need to inspect state.
 */
export { NEUTRAL_INTENT, createIntent, intentsEqual, isNeutralIntent, reverseHorizontal, facingToDirection, } from "./intent.js";
export { createHorizontalHeldProbe, createInputState, isHorizontalRequested, } from "./state.js";
export { applyIntentChange } from "./reducer.js";
export { createInputArbiter, } from "./arbiter.js";
export { createActivityTracker, } from "./activity.js";
export { DORMANT_STATE, stepAutopilot, } from "./Autopilot.js";
export { createAutopilotController, } from "./controller.js";
export { DEFAULT_AUTORUN_CONFIG, validateAutorunConfig, } from "./validation.js";
export { processDepthMovement, processHorizontalMovement, resetCamera, } from "./movement.js";
export { createKeyboardKeys, handleKeyDown, handleKeyUp, setupKeyboardControls, } from "./Keyboard.js";
export { DEFAULT_TOUCH_CONFIG, calculateDirection, createTouchState, directionToIntent, handleTouchEnd, handleTouchEndEvent, handleTouchMove, handleTouchStart, isTap, processDirectionChange, setupTouchControls, } from "./Touch.js";
export { createInputSystem, } from "./factory.js";
export { handleHopInput, handleHopRelease, handleJumpInput, handleWalkKeyDown, handleWalkKeyUp, isPendingJump, } from "./handlers.js";
//# sourceMappingURL=index.js.map