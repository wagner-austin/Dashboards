/**
 * Keyboard input source.
 *
 * Translates key presses into a MovementIntent and submits it to the arbiter.
 * The keyboard owns only its own held-key model; it never writes engine state,
 * so it cannot disagree with the touch or autopilot sources about what the
 * bunny is currently being told to do.
 */
import { createIntent, } from "./intent.js";
import { resetCamera } from "./movement.js";
/** Key that triggers a jump. */
const JUMP_KEY = " ";
/** Key that returns the camera to its starting position. */
const RESET_KEY = "r";
/** Movement keys, indexed by lower-cased KeyboardEvent.key. */
const KEY_BINDINGS = new Map([
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
export function createKeyboardKeys() {
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
function intentFromKeys(keys) {
    return createIntent(keys.horizontal, keys.vertical);
}
/**
 * Record a key press against the held-key model.
 *
 * Args:
 *     keys: Held-key model to update.
 *     binding: Axis and direction of the pressed key.
 */
function pressBinding(keys, binding) {
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
function releaseBinding(keys, binding) {
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
export function handleKeyDown(event, keys, deps) {
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
export function handleKeyUp(event, keys, deps) {
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
export function setupKeyboardControls(deps) {
    const keys = createKeyboardKeys();
    deps.events.addKeyListener("keydown", (event) => {
        handleKeyDown(event, keys, deps);
    });
    deps.events.addKeyListener("keyup", (event) => {
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
//# sourceMappingURL=Keyboard.js.map