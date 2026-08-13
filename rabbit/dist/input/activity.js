/**
 * User activity tracking.
 *
 * Measures how long the user has been idle so the autopilot knows when it may
 * engage and when it must stand down. Time is supplied by the caller as a
 * per-frame delta rather than read from a clock, so the autopilot's engage
 * threshold is exercised by tests with real arithmetic instead of timers.
 */
/**
 * Create an activity tracker starting at zero idle time.
 *
 * Returns:
 *     ActivityTracker with an idle time of zero.
 */
export function createActivityTracker() {
    let idle = 0;
    return {
        record() {
            idle = 0;
        },
        advance(deltaTime) {
            idle += deltaTime;
        },
        idleSeconds() {
            return idle;
        },
    };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    createActivityTracker,
};
//# sourceMappingURL=activity.js.map