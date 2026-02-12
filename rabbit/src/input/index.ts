/**
 * Input module public API.
 *
 * Re-exports keyboard and touch controls for external use.
 */

export {
  setupKeyboardControls,
  processDepthMovement,
  processHorizontalMovement,
  processInputChange,
  type InputState,
  type HorizontalInput,
  type VerticalInput,
} from "./Keyboard.js";

export {
  setupTouchControls,
  createTouchState,
  calculateDirection,
  isTap,
  processDirectionChange,
  handleTouchEnd,
  DEFAULT_TOUCH_CONFIG,
  type TouchState,
  type TouchConfig,
  type TouchDirection,
  type JoystickState,
} from "./Touch.js";

export {
  isPendingJump,
  handleJumpInput,
  handleWalkKeyDown,
  handleWalkKeyUp,
  handleHopInput,
  handleHopRelease,
} from "./handlers.js";
