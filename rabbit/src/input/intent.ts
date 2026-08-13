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

/** Horizontal movement request. */
export type HorizontalInput = "left" | "right" | null;

/** Vertical (depth) movement request. */
export type VerticalInput = "up" | "down" | null;

/** A horizontal direction with no neutral case. */
export type HorizontalDirection = "left" | "right";

/** A vertical direction with no neutral case. */
export type VerticalDirection = "up" | "down";

/**
 * Sources permitted to submit an intent.
 *
 * "user" outranks "autopilot": a non-neutral user intent always wins.
 */
export type IntentSource = "user" | "autopilot";

/**
 * An immutable snapshot of what one source wants the bunny to do.
 *
 * horizontal: Requested horizontal movement, or null for none.
 * vertical: Requested depth movement, or null for none.
 */
export interface MovementIntent {
  readonly horizontal: HorizontalInput;
  readonly vertical: VerticalInput;
}

/** Intent requesting no movement at all. */
export const NEUTRAL_INTENT: MovementIntent = { horizontal: null, vertical: null };

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
export function createIntent(
  horizontal: HorizontalInput,
  vertical: VerticalInput
): MovementIntent {
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
export function intentsEqual(a: MovementIntent, b: MovementIntent): boolean {
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
export function isNeutralIntent(intent: MovementIntent): boolean {
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
export function reverseHorizontal(direction: HorizontalDirection): HorizontalDirection {
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
export function facingToDirection(facingRight: boolean): HorizontalDirection {
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
