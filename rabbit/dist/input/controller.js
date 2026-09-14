/**
 * Autopilot controller - the mutable driver around the pure autopilot machine.
 *
 * Holds the autopilot's state between frames, keeps the idle timer honest, and
 * forwards the machine's output to the arbiter. All decision logic lives in
 * `stepAutopilot`; this module only sequences the side effects.
 */
import { DORMANT_STATE, stepAutopilot, } from "./Autopilot.js";
import { isNeutralIntent } from "./intent.js";
/**
 * Create an autopilot controller starting in the dormant phase.
 *
 * A held user intent keeps the idle timer pinned at zero, so a key held down
 * without repeat events still counts as continuous activity.
 *
 * Jump requests are issued before the intent is submitted: ending a walk leg
 * with a jump must reach the bunny while it is still walking, otherwise the
 * neutral intent would first send it into a walk-to-idle transition.
 *
 * Args:
 *     deps: Arbiter, idle timer, engine state, config, and random source.
 *
 * Returns:
 *     AutopilotController in the dormant phase.
 */
export function createAutopilotController(deps) {
    let phase = DORMANT_STATE;
    return {
        update(deltaTime) {
            if (isNeutralIntent(deps.arbiter.intentFor("user"))) {
                deps.activity.advance(deltaTime);
            }
            else {
                deps.activity.record();
            }
            const output = stepAutopilot(phase, {
                deltaTime,
                idleSeconds: deps.activity.idleSeconds(),
                facingRight: deps.state.bunny.facingRight,
            }, deps.config, deps.random);
            phase = output.state;
            if (output.jump) {
                deps.arbiter.requestJump("autopilot");
            }
            deps.arbiter.submit("autopilot", output.intent);
        },
        phase() {
            return phase;
        },
    };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    createAutopilotController,
};
//# sourceMappingURL=controller.js.map