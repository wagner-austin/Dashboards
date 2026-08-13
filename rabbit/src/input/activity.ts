/**
 * User activity tracking.
 *
 * Measures how long the user has been idle so the autopilot knows when it may
 * engage and when it must stand down. Time is supplied by the caller as a
 * per-frame delta rather than read from a clock, so the autopilot's engage
 * threshold is exercised by tests with real arithmetic instead of timers.
 */

/**
 * Tracks elapsed time since the last user action.
 */
export interface ActivityTracker {
  /** Reset the idle timer to zero. Called whenever the user acts. */
  readonly record: () => void;
  /** Advance the idle timer by one frame. */
  readonly advance: (deltaTime: number) => void;
  /** Seconds elapsed since the last recorded user action. */
  readonly idleSeconds: () => number;
}

/**
 * Create an activity tracker starting at zero idle time.
 *
 * Returns:
 *     ActivityTracker with an idle time of zero.
 */
export function createActivityTracker(): ActivityTracker {
  let idle = 0;

  return {
    record(): void {
      idle = 0;
    },
    advance(deltaTime: number): void {
      idle += deltaTime;
    },
    idleSeconds(): number {
      return idle;
    },
  };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  createActivityTracker,
};
