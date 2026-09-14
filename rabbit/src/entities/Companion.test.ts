import { describe, expect, it } from "vitest";
import { createCompanion, stepCompanion, companionFrame, _test_hooks, type CompanionState, type CompanionInput } from "./Companion.js";
import { createTestFrames } from "../testing/fixtures.js";

const STILL: CompanionInput = { deltaTime: 0.1, cameraDx: 0, cameraDz: 0, facingRight: false, jumping: false };

describe("companion pursuit", () => {
  it("remains at its following distance without mutating the input snapshot", () => {
    const initial = createCompanion();
    expect(stepCompanion(initial, STILL)).toStrictEqual({ ...initial, clock: 0.1 });
    expect(initial).toStrictEqual({ x: 115, z: 12, facingRight: false, mode: "idle", clock: 0, jumpTime: 0, wasLeaderJumping: false });
  });

  it("runs faster than the leader and then walks without overshooting", () => {
    const far = stepCompanion({ ...createCompanion(), x: 215 }, STILL);
    expect(far).toStrictEqual({ ...createCompanion(), x: 194, mode: "run" });
    const near = stepCompanion({ ...createCompanion(), x: 120 }, STILL);
    expect(near.x).toBe(115);
    expect(near.mode).toBe("walk");
    expect(stepCompanion(near, STILL).mode).toBe("settle");
  });

  it("keeps running through the catch-up band instead of flickering between gaits", () => {
    const running: CompanionState = { ...createCompanion(), x: 165, mode: "run" };
    const result = stepCompanion(running, STILL);
    expect(result.x).toBe(144);
    expect(result.mode).toBe("run");
    expect(stepCompanion({ ...running, x: 135 }, STILL).mode).toBe("walk");
  });

  it("follows a right-facing leader on the opposite side", () => {
    const result = stepCompanion({ ...createCompanion(), x: -250 }, { ...STILL, facingRight: true });
    expect(result.x).toBe(-229);
    expect(result.facingRight).toBe(true);
    expect(result.mode).toBe("run");
  });

  it("tracks depth displacement with an explicit turn before hopping", () => {
    const result = stepCompanion(createCompanion(), { ...STILL, cameraDz: 30 });
    expect(result.mode).toBe("turnAway");
    expect(result.z).toBe(-8);
    expect(result.facingRight).toBe(false);
    expect(stepCompanion({ ...result, clock: 0.3 }, STILL).mode).toBe("hopAway");
    expect(stepCompanion(createCompanion(), { ...STILL, cameraDz: -30 }).mode).toBe("turnToward");
  });

  it("triggers one jump per leader jump and lands after its full duration", () => {
    const launched = stepCompanion(createCompanion(), { ...STILL, jumping: true });
    expect(launched.jumpTime).toBe(0.5);
    expect(launched.mode).toBe("jump");
    const held = stepCompanion(launched, { ...STILL, jumping: true });
    expect(held.jumpTime).toBe(0.4);
    const airborne = stepCompanion({ ...held, wasLeaderJumping: false }, { ...STILL, jumping: true });
    expect(airborne.jumpTime).toBeCloseTo(0.3);
    let landed = airborne;
    for (let i = 0; i < 5; i++) landed = stepCompanion(landed, STILL);
    expect(landed.mode).toBe("idle");
    expect(landed.jumpTime).toBe(0);
  });

  it("bounds simulation time after suspension and rejects negative elapsed travel", () => {
    const initial = { ...createCompanion(), x: 215 };
    expect(stepCompanion(initial, { ...STILL, deltaTime: 20 }).x).toBe(194);
    expect(stepCompanion(initial, { ...STILL, deltaTime: -2 }).x).toBe(215);
  });
});

describe("companion animation selection", () => {
  const frames = createTestFrames();
  const sprint = { left: ["sprintL"], right: ["sprintR"] };
  const cases: readonly { mode: CompanionState["mode"]; left: string; right: string }[] = [
    { mode: "idle", left: "idleL0", right: "idleR0" },
    { mode: "walk", left: "walkL0", right: "walkR0" },
    { mode: "run", left: "sprintL", right: "sprintR" },
    { mode: "jump", left: "jumpL0", right: "jumpR0" },
    { mode: "settle", left: "transL0", right: "transR0" },
    { mode: "turnAway", left: "turnAwayL0", right: "turnAwayR0" },
    { mode: "turnToward", left: "turnTowardL0", right: "turnTowardR0" },
    { mode: "hopAway", left: "hopAway0", right: "hopAway0" },
    { mode: "hopToward", left: "hopToward0", right: "hopToward0" },
  ];
  for (const entry of cases) {
    it(`selects ${entry.mode} for both facings`, () => {
      expect(companionFrame({ ...createCompanion(), mode: entry.mode }, frames, sprint)).toStrictEqual([entry.left]);
      expect(companionFrame({ ...createCompanion(), mode: entry.mode, facingRight: true }, frames, sprint)).toStrictEqual([entry.right]);
    });
  }
  it("loops walking but holds the last transition pose", () => {
    expect(companionFrame({ ...createCompanion(), mode: "walk", clock: 0.13 }, frames, sprint)).toStrictEqual(["walkL1"]);
    expect(companionFrame({ ...createCompanion(), mode: "settle", clock: 2 }, frames, sprint)).toStrictEqual(["transL2"]);
    expect(() => companionFrame(createCompanion(), { ...frames, idleLeft: [] }, sprint)).toThrow("RABBIT_COMPANION_FRAME");
  });
  it("finishes turns and settling before choosing a new locomotion cycle", () => {
    const choose = _test_hooks.transitionMode;
    expect(choose({ ...createCompanion(), mode: "turnAway" }, "hopAway")).toBe("turnAway");
    expect(choose({ ...createCompanion(), mode: "turnToward" }, "hopToward")).toBe("turnToward");
    expect(choose({ ...createCompanion(), mode: "settle" }, "idle")).toBe("settle");
    expect(choose({ ...createCompanion(), mode: "turnToward", clock: 0.3 }, "hopToward")).toBe("hopToward");
    expect(choose({ ...createCompanion(), mode: "hopAway" }, "hopAway")).toBe("hopAway");
    expect(choose({ ...createCompanion(), mode: "hopToward" }, "hopToward")).toBe("hopToward");
    expect(choose({ ...createCompanion(), mode: "run" }, "idle")).toBe("settle");
    expect(choose({ ...createCompanion(), mode: "settle", clock: 0.3 }, "idle")).toBe("idle");
  });
});
