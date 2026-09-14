/**
 * Autopilot controller - the mutable driver around the pure autopilot machine.
 *
 * Holds the autopilot's state between frames, keeps the idle timer honest, and
 * forwards the machine's output to the arbiter. All decision logic lives in
 * `stepAutopilot`; this module only sequences the side effects.
 */

import type { ActivityTracker } from "./activity.js";
import type { InputArbiter } from "./arbiter.js";
import {
  DORMANT_STATE,
  stepAutopilot,
  type AutopilotState,
  type RandomSource,
} from "./Autopilot.js";
import { isNeutralIntent } from "./intent.js";
import type { InputState } from "./state.js";
import type { AutorunConfig } from "./validation.js";

/**
 * Dependencies required to drive the autopilot each frame.
 *
 * arbiter: Receives the autopilot's intent and jump requests.
 * activity: Idle timer consulted for the engage threshold.
 * state: Engine state, read for the bunny's current facing.
 * config: Autorun tuning values.
 * random: Source of draws in [0, 1) shaping the wander.
 */
export interface AutopilotDeps {
  readonly arbiter: InputArbiter;
  readonly activity: ActivityTracker;
  readonly state: InputState;
  readonly config: AutorunConfig;
  readonly random: RandomSource;
}

/**
 * Frame-driven autopilot.
 */
export interface AutopilotController {
  /** Advance the autopilot one frame. */
  readonly update: (deltaTime: number) => void;
  /** Current autopilot phase, for inspection. */
  readonly phase: () => AutopilotState;
}

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
export function createAutopilotController(deps: AutopilotDeps): AutopilotController {
  let phase: AutopilotState = DORMANT_STATE;

  return {
    update(deltaTime: number): void {
      if (isNeutralIntent(deps.arbiter.intentFor("user"))) {
        deps.activity.advance(deltaTime);
      } else {
        deps.activity.record();
      }

      const output = stepAutopilot(
        phase,
        {
          deltaTime,
          idleSeconds: deps.activity.idleSeconds(),
          facingRight: deps.state.bunny.facingRight,
        },
        deps.config,
        deps.random
      );

      phase = output.state;

      if (output.jump) {
        deps.arbiter.requestJump("autopilot");
      }

      deps.arbiter.submit("autopilot", output.intent);
    },

    phase(): AutopilotState {
      return phase;
    },
  };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  createAutopilotController,
};
