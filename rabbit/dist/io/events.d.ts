/**
 * DOM event adapters for the input layer.
 *
 * The input sources depend on the narrow KeyboardEventSource and
 * TouchEventSource interfaces; these are the only implementations that touch
 * the document. Excluded from unit test coverage as an I/O boundary - the
 * behaviour behind them is exercised through dependency injection.
 */
import type { KeyboardEventSource } from "../input/Keyboard.js";
import type { TouchEventSource } from "../input/Touch.js";
/**
 * Create a keyboard event source bound to the document.
 *
 * Returns:
 *     KeyboardEventSource registering listeners on the document.
 */
export declare function createDocumentKeyboardSource(): KeyboardEventSource;
/**
 * Create a touch event source bound to the document.
 *
 * Returns:
 *     TouchEventSource registering listeners on the document and reading the
 *     wall clock for tap detection.
 */
export declare function createDocumentTouchSource(): TouchEventSource;
//# sourceMappingURL=events.d.ts.map