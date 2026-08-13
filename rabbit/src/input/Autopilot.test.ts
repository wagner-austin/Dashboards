/**
 * Tests for the autopilot supervisory state machine.
 *
 * `stepAutopilot` is pure, so every case here drives it with a real sequence of
 * draws and asserts on the returned state and intent. The draw order each
 * helper consumes is part of the contract and is asserted directly.
 */

import { describe, it, expect } from "vitest";
import { _test_hooks, type AutopilotState, type HopState, type WalkState } from "./Autopilot.js";
import type { AutorunConfig } from "./validation.js";
import { createSequenceRandom, createConstantRandom } from "../testing/fixtures.js";

const {
  randomRange,
  intentOf,
  withRemaining,
  beginPause,
  chooseWalkDirection,
  beginLeg,
  outputOf,
  endLeg,
  stepAutopilot,
  DORMANT_STATE,
} = _test_hooks;

/** Config with wide, easily-checked ranges. */
const BASE: AutorunConfig = {
  enabled: true,
  idleDelay: 5,
  minLeg: 2,
  maxLeg: 6,
  minPause: 1,
  maxPause: 3,
  turnChance: 0.5,
  hopChance: 0.25,
  jumpChance: 0.2,
};

/**
 * Build autopilot input with defaults for the fields a test ignores.
 *
 * Args:
 *     deltaTime: Seconds elapsed this frame.
 *     idleSeconds: Seconds since the user last acted.
 *     facingRight: Direction the bunny faces.
 *
 * Returns:
 *     AutopilotInput for stepAutopilot.
 */
function input(
  deltaTime: number,
  idleSeconds: number,
  facingRight = false
): { deltaTime: number; idleSeconds: number; facingRight: boolean } {
  return { deltaTime, idleSeconds, facingRight };
}

describe("randomRange", () => {
  it("returns the minimum for a zero draw", () => {
    expect(randomRange(createConstantRandom(0), 2, 6)).toBe(2);
  });

  it("returns the midpoint for a half draw", () => {
    expect(randomRange(createConstantRandom(0.5), 2, 6)).toBe(4);
  });

  it("returns the minimum for a degenerate range", () => {
    expect(randomRange(createConstantRandom(0.9), 3, 3)).toBe(3);
  });
});

describe("intentOf", () => {
  it("maps dormant to no movement", () => {
    expect(intentOf(DORMANT_STATE)).toStrictEqual({ horizontal: null, vertical: null });
  });

  it("maps pause to no movement", () => {
    expect(intentOf({ kind: "pause", remaining: 1 })).toStrictEqual({
      horizontal: null,
      vertical: null,
    });
  });

  it("maps walk to its horizontal direction", () => {
    expect(intentOf({ kind: "walk", direction: "right", remaining: 1 })).toStrictEqual({
      horizontal: "right",
      vertical: null,
    });
  });

  it("maps hop to its vertical direction", () => {
    expect(intentOf({ kind: "hop", direction: "down", remaining: 1 })).toStrictEqual({
      horizontal: null,
      vertical: "down",
    });
  });
});

describe("withRemaining", () => {
  it("rebuilds a pause", () => {
    expect(withRemaining({ kind: "pause", remaining: 5 }, 2)).toStrictEqual({
      kind: "pause",
      remaining: 2,
    });
  });

  it("rebuilds a walk keeping its direction", () => {
    expect(withRemaining({ kind: "walk", direction: "left", remaining: 5 }, 2)).toStrictEqual({
      kind: "walk",
      direction: "left",
      remaining: 2,
    });
  });

  it("rebuilds a hop keeping its direction", () => {
    expect(withRemaining({ kind: "hop", direction: "up", remaining: 5 }, 2)).toStrictEqual({
      kind: "hop",
      direction: "up",
      remaining: 2,
    });
  });
});

describe("beginPause", () => {
  it("draws the pause duration from the configured range", () => {
    expect(beginPause(BASE, createSequenceRandom([0.5]))).toStrictEqual({
      kind: "pause",
      remaining: 2,
    });
  });
});

describe("chooseWalkDirection", () => {
  it("keeps the current direction when the turn roll fails", () => {
    expect(chooseWalkDirection(true, BASE, createSequenceRandom([0.8]))).toBe("right");
    expect(chooseWalkDirection(false, BASE, createSequenceRandom([0.8]))).toBe("left");
  });

  it("reverses when the turn roll succeeds", () => {
    expect(chooseWalkDirection(true, BASE, createSequenceRandom([0.2]))).toBe("left");
    expect(chooseWalkDirection(false, BASE, createSequenceRandom([0.2]))).toBe("right");
  });

  it("never turns at a zero turn chance", () => {
    const config: AutorunConfig = { ...BASE, turnChance: 0 };
    expect(chooseWalkDirection(true, config, createSequenceRandom([0]))).toBe("right");
  });
});

describe("beginLeg", () => {
  it("draws duration, then the hop roll, then the turn roll for a walk", () => {
    const leg = beginLeg(false, BASE, createSequenceRandom([0.5, 0.9, 0.8]));
    expect(leg).toStrictEqual({ kind: "walk", direction: "left", remaining: 4 });
  });

  it("draws duration, then the hop roll, then the direction roll for a hop", () => {
    const leg = beginLeg(false, BASE, createSequenceRandom([0.25, 0.1, 0.4]));
    expect(leg).toStrictEqual({ kind: "hop", direction: "up", remaining: 3 });
  });

  it("hops toward the viewer on a high direction roll", () => {
    const leg = beginLeg(false, BASE, createSequenceRandom([0.25, 0.1, 0.7]));
    expect(leg).toStrictEqual({ kind: "hop", direction: "down", remaining: 3 });
  });

  it("never hops at a zero hop chance", () => {
    const config: AutorunConfig = { ...BASE, hopChance: 0 };
    const leg = beginLeg(true, config, createSequenceRandom([0.5, 0, 0.9]));
    expect(leg.kind).toBe("walk");
  });

  it("always hops at a hop chance of one", () => {
    const config: AutorunConfig = { ...BASE, hopChance: 1 };
    const leg = beginLeg(true, config, createSequenceRandom([0.5, 0.99, 0.1]));
    expect(leg.kind).toBe("hop");
  });
});

describe("outputOf", () => {
  it("pairs a state with its intent and no jump", () => {
    expect(outputOf({ kind: "walk", direction: "right", remaining: 3 })).toStrictEqual({
      state: { kind: "walk", direction: "right", remaining: 3 },
      intent: { horizontal: "right", vertical: null },
      jump: false,
    });
  });
});

describe("endLeg", () => {
  const walk: WalkState = { kind: "walk", direction: "left", remaining: 0 };
  const hop: HopState = { kind: "hop", direction: "up", remaining: 0 };

  it("jumps out of a walk when the jump roll succeeds", () => {
    const output = endLeg(walk, BASE, createSequenceRandom([0.1, 0.5]));
    expect(output.jump).toBe(true);
    expect(output.state).toStrictEqual({ kind: "pause", remaining: 2 });
    expect(output.intent).toStrictEqual({ horizontal: null, vertical: null });
  });

  it("does not jump out of a walk when the jump roll fails", () => {
    const output = endLeg(walk, BASE, createSequenceRandom([0.9, 0.5]));
    expect(output.jump).toBe(false);
  });

  it("never jumps out of a hop and skips the jump roll", () => {
    const output = endLeg(hop, BASE, createSequenceRandom([0.5]));
    expect(output.jump).toBe(false);
    expect(output.state).toStrictEqual({ kind: "pause", remaining: 2 });
  });
});

describe("stepAutopilot", () => {
  it("stands down while autorun is disabled, however idle the user is", () => {
    const config: AutorunConfig = { ...BASE, enabled: false };
    const output = stepAutopilot(
      { kind: "walk", direction: "left", remaining: 3 },
      input(0.016, 9999),
      config,
      createSequenceRandom([])
    );

    expect(output.state).toStrictEqual(DORMANT_STATE);
    expect(output.intent).toStrictEqual({ horizontal: null, vertical: null });
    expect(output.jump).toBe(false);
  });

  it("stands down while the user is more recent than the idle delay", () => {
    const output = stepAutopilot(DORMANT_STATE, input(0.016, 4.9), BASE, createSequenceRandom([]));
    expect(output.state).toStrictEqual(DORMANT_STATE);
  });

  it("abandons an active leg the moment the user acts", () => {
    const output = stepAutopilot(
      { kind: "walk", direction: "right", remaining: 3 },
      input(0.016, 0),
      BASE,
      createSequenceRandom([])
    );

    expect(output.state).toStrictEqual(DORMANT_STATE);
    expect(output.intent).toStrictEqual({ horizontal: null, vertical: null });
  });

  it("engages into a leg exactly at the idle delay", () => {
    const output = stepAutopilot(
      DORMANT_STATE,
      input(0.016, 5),
      BASE,
      createSequenceRandom([0.5, 0.9, 0.8])
    );

    expect(output.state).toStrictEqual({ kind: "walk", direction: "left", remaining: 4 });
    expect(output.intent).toStrictEqual({ horizontal: "left", vertical: null });
  });

  it("engages walking the way the bunny already faces", () => {
    const output = stepAutopilot(
      DORMANT_STATE,
      input(0.016, 10, true),
      BASE,
      createSequenceRandom([0.5, 0.9, 0.8])
    );

    expect(output.state).toStrictEqual({ kind: "walk", direction: "right", remaining: 4 });
  });

  it("counts down an active leg without drawing", () => {
    const output = stepAutopilot(
      { kind: "walk", direction: "right", remaining: 3 },
      input(0.5, 10),
      BASE,
      createSequenceRandom([])
    );

    expect(output.state).toStrictEqual({ kind: "walk", direction: "right", remaining: 2.5 });
    expect(output.intent).toStrictEqual({ horizontal: "right", vertical: null });
  });

  it("counts down a pause without drawing", () => {
    const output = stepAutopilot(
      { kind: "pause", remaining: 2 },
      input(0.5, 10),
      BASE,
      createSequenceRandom([])
    );

    expect(output.state).toStrictEqual({ kind: "pause", remaining: 1.5 });
  });

  it("starts a new leg when a pause expires", () => {
    const output = stepAutopilot(
      { kind: "pause", remaining: 0.25 },
      input(0.5, 10),
      BASE,
      createSequenceRandom([0.25, 0.1, 0.4])
    );

    expect(output.state).toStrictEqual({ kind: "hop", direction: "up", remaining: 3 });
    expect(output.intent).toStrictEqual({ horizontal: null, vertical: "up" });
  });

  it("drops into a pause when a walk leg expires", () => {
    const output = stepAutopilot(
      { kind: "walk", direction: "left", remaining: 0.25 },
      input(0.5, 10),
      BASE,
      createSequenceRandom([0.9, 0.5])
    );

    expect(output.state).toStrictEqual({ kind: "pause", remaining: 2 });
    expect(output.intent).toStrictEqual({ horizontal: null, vertical: null });
    expect(output.jump).toBe(false);
  });

  it("drops into a pause when a hop leg expires", () => {
    const output = stepAutopilot(
      { kind: "hop", direction: "down", remaining: 0.25 },
      input(0.5, 10),
      BASE,
      createSequenceRandom([0.5])
    );

    expect(output.state).toStrictEqual({ kind: "pause", remaining: 2 });
  });

  it("treats a leg reaching exactly zero as expired", () => {
    const output = stepAutopilot(
      { kind: "walk", direction: "left", remaining: 0.5 },
      input(0.5, 10),
      BASE,
      createSequenceRandom([0.9, 0.5])
    );

    expect(output.state.kind).toBe("pause");
  });

  it("wanders through walk, pause, and hop across many frames", () => {
    // Draws: leg(4, walk, keep) -> jump roll fail, pause(2) -> leg(3, hop, up)
    const random = createSequenceRandom([0.5, 0.9, 0.8, 0.9, 0.5, 0.25, 0.1, 0.4]);
    let state: AutopilotState = DORMANT_STATE;
    const kinds: string[] = [];

    for (let frame = 0; frame < 16; frame += 1) {
      const output = stepAutopilot(state, input(0.5, 10), BASE, random);
      state = output.state;
      kinds.push(state.kind);
    }

    expect(kinds[0]).toBe("walk");
    expect(kinds).toContain("pause");
    expect(kinds[kinds.length - 1]).toBe("hop");
  });
});
