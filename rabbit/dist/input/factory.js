/**
 * Input system factory.
 *
 * Builds the focused services of the input layer and wires them together:
 * arbiter, idle tracker, autopilot, keyboard, and touch. Callers get one
 * `update` to call per frame and never see the internal wiring, so the layer
 * can grow another source without changing the render loop.
 */
import { createActivityTracker } from "./activity.js";
import { createInputArbiter } from "./arbiter.js";
import { createAutopilotController } from "./controller.js";
import { setupKeyboardControls, } from "./Keyboard.js";
import { processDepthMovement, processHorizontalMovement, } from "./movement.js";
import { setupTouchControls, } from "./Touch.js";
/**
 * Build and wire the input layer.
 *
 * Args:
 *     deps: Engine state, animation data, configuration, and event targets.
 *
 * Returns:
 *     InputSystem with keyboard and touch listeners already bound.
 */
export function createInputSystem(deps) {
    const arbiter = createInputArbiter({
        state: deps.state,
        frames: deps.frames,
        timers: deps.timers,
    });
    const activity = createActivityTracker();
    const autopilot = createAutopilotController({
        arbiter,
        activity,
        state: deps.state,
        config: deps.autorun,
        random: deps.random,
    });
    const keys = setupKeyboardControls({
        state: deps.state,
        arbiter,
        activity,
        events: deps.keyboardEvents,
    });
    const touchState = setupTouchControls({
        arbiter,
        activity,
        events: deps.touchEvents,
        config: deps.touch,
    });
    return {
        arbiter,
        activity,
        autopilot,
        keys,
        touchState,
        update(deltaTime) {
            autopilot.update(deltaTime);
            processDepthMovement(deps.state, deltaTime, deps.speeds.depth);
            processHorizontalMovement(deps.state, deltaTime, deps.speeds.horizontal);
        },
    };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    createInputSystem,
};
//# sourceMappingURL=factory.js.map