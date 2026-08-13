/**
 * Input module public API.
 *
 * The layer is assembled by `createInputSystem`; the individual services are
 * exported for tests and for callers that need to inspect state.
 */
export { NEUTRAL_INTENT, createIntent, intentsEqual, isNeutralIntent, reverseHorizontal, facingToDirection, type HorizontalInput, type VerticalInput, type HorizontalDirection, type VerticalDirection, type IntentSource, type MovementIntent, } from "./intent.js";
export { createHorizontalHeldProbe, createInputState, isHorizontalRequested, type InputState, } from "./state.js";
export { applyIntentChange } from "./reducer.js";
export { createInputArbiter, type ArbiterDeps, type InputArbiter, } from "./arbiter.js";
export { createActivityTracker, type ActivityTracker, } from "./activity.js";
export { DORMANT_STATE, stepAutopilot, type AutopilotInput, type AutopilotOutput, type AutopilotState, type RandomSource, type TimedState, } from "./Autopilot.js";
export { createAutopilotController, type AutopilotController, type AutopilotDeps, } from "./controller.js";
export { DEFAULT_AUTORUN_CONFIG, validateAutorunConfig, type AutorunConfig, } from "./validation.js";
export { processDepthMovement, processHorizontalMovement, resetCamera, } from "./movement.js";
export { createKeyboardKeys, handleKeyDown, handleKeyUp, setupKeyboardControls, type AxisBinding, type KeyEventType, type KeyboardDeps, type KeyboardEventSource, type KeyboardKeys, } from "./Keyboard.js";
export { DEFAULT_TOUCH_CONFIG, calculateDirection, createTouchState, directionToIntent, handleTouchEnd, handleTouchEndEvent, handleTouchMove, handleTouchStart, isTap, processDirectionChange, setupTouchControls, type JoystickState, type TouchConfig, type TouchDeps, type TouchDirection, type TouchEventSource, type TouchEventType, type TouchPoint, type TouchState, } from "./Touch.js";
export { createInputSystem, type InputSystem, type InputSystemDeps, } from "./factory.js";
export { handleHopInput, handleHopRelease, handleJumpInput, handleWalkKeyDown, handleWalkKeyUp, isPendingJump, } from "./handlers.js";
//# sourceMappingURL=index.d.ts.map