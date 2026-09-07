/**
 * DOM event adapters for the input layer.
 *
 * The input sources depend on the narrow KeyboardEventSource and
 * TouchEventSource interfaces; these are the only implementations that touch
 * the document.
 */
import type { KeyboardEventSource } from "../input/Keyboard.js";
import type { TouchEventSource, TouchPoint } from "../input/Touch.js";
/**
 * Create a keyboard event source bound to the document.
 *
 * Returns:
 *     KeyboardEventSource registering listeners on the document.
 */
export declare function createDocumentKeyboardSource(): KeyboardEventSource;
/**
 * Read the active touch points out of a DOM touch event.
 *
 * This is the parse-at-the-edge step: DOM Touch objects already carry the
 * three fields TouchPoint declares, so the input layer never sees a TouchList.
 *
 * Args:
 *     event: The DOM touch event.
 *
 * Returns:
 *     The event's active touch points.
 */
declare function readTouchPoints(event: TouchEvent): readonly TouchPoint[];
/**
 * Create a touch event source bound to the document.
 *
 * Returns:
 *     TouchEventSource registering listeners on the document and reading the
 *     wall clock for tap detection.
 */
export declare function createDocumentTouchSource(): TouchEventSource;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    readTouchPoints: typeof readTouchPoints;
};
export {};
//# sourceMappingURL=events.d.ts.map