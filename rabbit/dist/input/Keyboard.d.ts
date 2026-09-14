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
import { type HorizontalDirection, type HorizontalInput, type MovementIntent, type VerticalDirection, type VerticalInput } from "./intent.js";
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
    readonly addKeyListener: (type: KeyEventType, handler: (event: KeyboardEvent) => void) => void;
}
/** A key bound to one axis of movement. */
export type AxisBinding = {
    readonly axis: "horizontal";
    readonly value: HorizontalDirection;
} | {
    readonly axis: "vertical";
    readonly value: VerticalDirection;
};
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
/**
 * Create the held-key model with nothing pressed.
 *
 * Returns:
 *     KeyboardKeys with both axes released.
 */
export declare function createKeyboardKeys(): KeyboardKeys;
/**
 * Convert held keys into a movement intent.
 *
 * Args:
 *     keys: Currently held keys.
 *
 * Returns:
 *     The intent those keys request.
 */
declare function intentFromKeys(keys: KeyboardKeys): MovementIntent;
/**
 * Record a key press against the held-key model.
 *
 * Args:
 *     keys: Held-key model to update.
 *     binding: Axis and direction of the pressed key.
 */
declare function pressBinding(keys: KeyboardKeys, binding: AxisBinding): void;
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
declare function releaseBinding(keys: KeyboardKeys, binding: AxisBinding): boolean;
/**
 * Handle a key press.
 *
 * Args:
 *     event: The keydown event.
 *     keys: Held-key model to update.
 *     deps: Keyboard dependencies.
 */
export declare function handleKeyDown(event: KeyboardEvent, keys: KeyboardKeys, deps: KeyboardDeps): void;
/**
 * Handle a key release.
 *
 * Args:
 *     event: The keyup event.
 *     keys: Held-key model to update.
 *     deps: Keyboard dependencies.
 */
export declare function handleKeyUp(event: KeyboardEvent, keys: KeyboardKeys, deps: KeyboardDeps): void;
/**
 * Bind keyboard listeners and start producing intent.
 *
 * Args:
 *     deps: Keyboard dependencies.
 *
 * Returns:
 *     The held-key model this source maintains.
 */
export declare function setupKeyboardControls(deps: KeyboardDeps): KeyboardKeys;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createKeyboardKeys: typeof createKeyboardKeys;
    intentFromKeys: typeof intentFromKeys;
    pressBinding: typeof pressBinding;
    releaseBinding: typeof releaseBinding;
    handleKeyDown: typeof handleKeyDown;
    handleKeyUp: typeof handleKeyUp;
    setupKeyboardControls: typeof setupKeyboardControls;
    KEY_BINDINGS: ReadonlyMap<string, AxisBinding>;
    JUMP_KEY: string;
    RESET_KEY: string;
};
export {};
//# sourceMappingURL=Keyboard.d.ts.map