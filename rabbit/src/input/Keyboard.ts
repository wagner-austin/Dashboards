/**
 * Keyboard input source.
 *
 * Translates key presses into a MovementIntent and submits it to the arbiter.
 * The keyboard owns only its own held-key model; it never writes engine state,
 * so it cannot disagree with the touch or autopilot sources about what the
 * bunny is currently being told to do.
 */

import type { ActivityTracker } from "./activity.js";
import type { InputArbiter } from "./arbiter.js";
import {
  createIntent,
  type HorizontalDirection,
  type HorizontalInput,
  type MovementIntent,
  type VerticalDirection,
  type VerticalInput,
} from "./intent.js";
import { resetCamera } from "./movement.js";
import type { InputState } from "./state.js";

/** Keyboard event types this source binds to. */
export type KeyEventType = "keydown" | "keyup";

/**
 * Minimal interface over the event target the keyboard binds to.
 *
 * Narrower than EventTarget on purpose: the input layer needs exactly this
 * much of the DOM, and nothing here forces a browser to exist.
 */
export interface KeyboardEventSource {
  readonly addKeyListener: (
    type: KeyEventType,
    handler: (event: KeyboardEvent) => void
  ) => void;
}

/** A key bound to one axis of movement. */
export type AxisBinding =
  | { readonly axis: "horizontal"; readonly value: HorizontalDirection }
  | { readonly axis: "vertical"; readonly value: VerticalDirection };

/**
 * Keys the user is currently holding.
 *
 * horizontal: Held horizontal direction, or null.
 * vertical: Held depth direction, or null.
 */
export interface KeyboardKeys {
  horizontal: HorizontalInput;
  vertical: VerticalInput;
}

/**
 * Dependencies required to run the keyboard source.
 *
 * state: Engine state, used for the camera reset key.
 * arbiter: Receives this source's intent and jump requests.
 * activity: Idle timer reset on every key press.
 * events: Event target to bind listeners to.
 */
export interface KeyboardDeps {
  readonly state: InputState;
  readonly arbiter: InputArbiter;
  readonly activity: ActivityTracker;
  readonly events: KeyboardEventSource;
}

/** Key that triggers a jump. */
const JUMP_KEY = " ";

/** Key that returns the camera to its starting position. */
const RESET_KEY = "r";

/** Movement keys, indexed by lower-cased KeyboardEvent.key. */
const KEY_BINDINGS: ReadonlyMap<string, AxisBinding> = new Map<string, AxisBinding>([
  ["arrowleft", { axis: "horizontal", value: "left" }],
  ["a", { axis: "horizontal", value: "left" }],
  ["arrowright", { axis: "horizontal", value: "right" }],
  ["d", { axis: "horizontal", value: "right" }],
  ["arrowup", { axis: "vertical", value: "up" }],
  ["w", { axis: "vertical", value: "up" }],
  ["arrowdown", { axis: "vertical", value: "down" }],
  ["s", { axis: "vertical", value: "down" }],
]);

/**
 * Create the held-key model with nothing pressed.
 *
 * Returns:
 *     KeyboardKeys with both axes released.
 */
export function createKeyboardKeys(): KeyboardKeys {
  return { horizontal: null, vertical: null };
}

/**
 * Convert held keys into a movement intent.
 *
 * Args:
 *     keys: Currently held keys.
 *
 * Returns:
 *     The intent those keys request.
 */
function intentFromKeys(keys: KeyboardKeys): MovementIntent {
  return createIntent(keys.horizontal, keys.vertical);
}

/**
 * Record a key press against the held-key model.
 *
 * Args:
 *     keys: Held-key model to update.
 *     binding: Axis and direction of the pressed key.
 */
function pressBinding(keys: KeyboardKeys, binding: AxisBinding): void {
  if (binding.axis === "horizontal") {
    keys.horizontal = binding.value;
    return;
  }
  keys.vertical = binding.value;
}

/**
 * Record a key release against the held-key model.
 *
 * A release only clears the axis if that exact direction is the one currently
 * held, so releasing a key that was already overridden changes nothing.
 *
 * Args:
 *     keys: Held-key model to update.
 *     binding: Axis and direction of the released key.
 *
 * Returns:
 *     True if the axis was cleared.
 */
function releaseBinding(keys: KeyboardKeys, binding: AxisBinding): boolean {
  if (binding.axis === "horizontal") {
    if (keys.horizontal !== binding.value) {
      return false;
    }
    keys.horizontal = null;
    return true;
  }
  if (keys.vertical !== binding.value) {
    return false;
  }
  keys.vertical = null;
  return true;
}

/**
 * Handle a key press.
 *
 * Args:
 *     event: The keydown event.
 *     keys: Held-key model to update.
 *     deps: Keyboard dependencies.
 */
export function handleKeyDown(
  event: KeyboardEvent,
  keys: KeyboardKeys,
  deps: KeyboardDeps
): void {
  deps.activity.record();

  if (event.repeat) {
    return;
  }

  const key = event.key.toLowerCase();

  if (key === JUMP_KEY) {
    deps.arbiter.requestJump("user");
    event.preventDefault();
    return;
  }

  if (key === RESET_KEY) {
    resetCamera(deps.state);
    return;
  }

  const binding = KEY_BINDINGS.get(key);
  if (binding === undefined) {
    return;
  }

  pressBinding(keys, binding);
  deps.arbiter.submit("user", intentFromKeys(keys));
}

/**
 * Handle a key release.
 *
 * Args:
 *     event: The keyup event.
 *     keys: Held-key model to update.
 *     deps: Keyboard dependencies.
 */
export function handleKeyUp(
  event: KeyboardEvent,
  keys: KeyboardKeys,
  deps: KeyboardDeps
): void {
  const binding = KEY_BINDINGS.get(event.key.toLowerCase());
  if (binding === undefined) {
    return;
  }

  if (!releaseBinding(keys, binding)) {
    return;
  }

  deps.activity.record();
  deps.arbiter.submit("user", intentFromKeys(keys));
}

/**
 * Bind keyboard listeners and start producing intent.
 *
 * Args:
 *     deps: Keyboard dependencies.
 *
 * Returns:
 *     The held-key model this source maintains.
 */
export function setupKeyboardControls(deps: KeyboardDeps): KeyboardKeys {
  const keys = createKeyboardKeys();

  deps.events.addKeyListener("keydown", (event: KeyboardEvent) => {
    handleKeyDown(event, keys, deps);
  });

  deps.events.addKeyListener("keyup", (event: KeyboardEvent) => {
    handleKeyUp(event, keys, deps);
  });

  return keys;
}

/** Test hooks for internal functions */
export const _test_hooks = {
  createKeyboardKeys,
  intentFromKeys,
  pressBinding,
  releaseBinding,
  handleKeyDown,
  handleKeyUp,
  setupKeyboardControls,
  KEY_BINDINGS,
  JUMP_KEY,
  RESET_KEY,
};
