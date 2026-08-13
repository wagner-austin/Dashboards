/**
 * Movement intent - the typed boundary between input sources and the engine.
 *
 * Keyboard, touch, and the autopilot never mutate engine state directly.
 * Each produces a MovementIntent describing what it wants the bunny to do,
 * and the arbiter resolves competing intents into the single effective one.
 * Adding a fourth source therefore cannot introduce a second writer.
 *
 * This module is a leaf: it imports nothing, so configuration validation and
 * the autopilot state machine can depend on it without creating cycles.
 */
/** Intent requesting no movement at all. */
export const NEUTRAL_INTENT = { horizontal: null, vertical: null };
/**
 * Create a movement intent.
 *
 * Args:
 *     horizontal: Requested horizontal movement.
 *     vertical: Requested depth movement.
 *
 * Returns:
 *     A new immutable MovementIntent.
 */
export function createIntent(horizontal, vertical) {
    return { horizontal, vertical };
}
/**
 * Compare two intents by value.
 *
 * Args:
 *     a: First intent.
 *     b: Second intent.
 *
 * Returns:
 *     True if both axes match.
 */
export function intentsEqual(a, b) {
    return a.horizontal === b.horizontal && a.vertical === b.vertical;
}
/**
 * Check whether an intent requests no movement.
 *
 * Args:
 *     intent: Intent to inspect.
 *
 * Returns:
 *     True if both axes are null.
 */
export function isNeutralIntent(intent) {
    return intent.horizontal === null && intent.vertical === null;
}
/**
 * Reverse a horizontal direction.
 *
 * Args:
 *     direction: Direction to reverse.
 *
 * Returns:
 *     The opposite direction.
 */
export function reverseHorizontal(direction) {
    return direction === "left" ? "right" : "left";
}
/**
 * Convert a facing flag into a horizontal direction.
 *
 * Args:
 *     facingRight: True when the bunny faces right.
 *
 * Returns:
 *     The matching horizontal direction.
 */
export function facingToDirection(facingRight) {
    return facingRight ? "right" : "left";
}
/** Test hooks for internal functions */
export const _test_hooks = {
    createIntent,
    intentsEqual,
    isNeutralIntent,
    reverseHorizontal,
    facingToDirection,
    NEUTRAL_INTENT,
};
//# sourceMappingURL=intent.js.map