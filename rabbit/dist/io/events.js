/**
 * DOM event adapters for the input layer.
 *
 * The input sources depend on the narrow KeyboardEventSource and
 * TouchEventSource interfaces; these are the only implementations that touch
 * the document. Excluded from unit test coverage as an I/O boundary - the
 * behaviour behind them is exercised through dependency injection.
 */
/**
 * Create a keyboard event source bound to the document.
 *
 * Returns:
 *     KeyboardEventSource registering listeners on the document.
 */
export function createDocumentKeyboardSource() {
    return {
        addKeyListener: (type, handler) => {
            document.addEventListener(type, handler);
        },
    };
}
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
function readTouchPoints(event) {
    return Array.from(event.touches);
}
/**
 * Create a touch event source bound to the document.
 *
 * Returns:
 *     TouchEventSource registering listeners on the document and reading the
 *     wall clock for tap detection.
 */
export function createDocumentTouchSource() {
    return {
        addTouchListener: (type, handler, passive) => {
            document.addEventListener(type, (event) => {
                if (handler(readTouchPoints(event))) {
                    event.preventDefault();
                }
            }, { passive });
        },
        now: () => Date.now(),
    };
}
//# sourceMappingURL=events.js.map