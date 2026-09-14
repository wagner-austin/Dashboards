import { describe, expect, it } from "vitest";
import { createAdventure, type AdventureAssets } from "./Adventure.js";
import { createTestFrames, createTestBunnyState } from "../testing/fixtures.js";

const ASSETS: AdventureAssets = { companion: createTestFrames(), alertLeft: ["lowL", "highL"], alertRight: ["lowR", "highR"], lionSprint: { left: ["runL"], right: ["runR"] } };
const CAMERA = { x: 0, z: 0 };

describe("adventure service", () => {
  it("raises the rabbit during rest, holds its final pose, and releases on movement", () => {
    const service = createAdventure(ASSETS, "bunny", CAMERA, 160);
    const idle = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    expect(service.update(0.6, CAMERA, idle, false).alert).toBeNull();
    expect(service.update(0.1, CAMERA, idle, false).alert).toStrictEqual(["lowL"]);
    const final = service.update(3, CAMERA, idle, false);
    expect(final.alert).toStrictEqual(["highL"]);
    expect(final.status).toBe("Rabbit is looking around");
    expect(final.companionColor).toBe("#58baff");
    expect(service.update(0.1, CAMERA, { ...idle, facingRight: true }, false).alert).toStrictEqual(["highR"]);
    expect(service.update(0.1, CAMERA, createTestBunnyState({ kind: "walk", frameIdx: 0 }), false).alert).toBeNull();
  });
  it("uses sprint art only for a sprinting lion's side movement", () => {
    const service = createAdventure(ASSETS, "lion", CAMERA, 160);
    const walk = createTestBunnyState({ kind: "walk", frameIdx: 0 });
    expect(service.update(0.1, CAMERA, walk, true).alert).toStrictEqual(["runL"]);
    expect(service.update(0.1, CAMERA, { ...walk, facingRight: true }, true).alert).toStrictEqual(["runR"]);
    const idle = service.update(1, CAMERA, createTestBunnyState({ kind: "idle", frameIdx: 0 }), true);
    expect(idle.alert).toBeNull();
    expect(idle.companionColor).toBe("#ffffff");
    expect(idle.companionSprint).toStrictEqual({ left: ASSETS.companion.walkLeft, right: ASSETS.companion.walkRight });
  });
  it("distinguishes running, jumping together, and idle status", () => {
    const service = createAdventure(ASSETS, "bunny", CAMERA, 160);
    const walk = createTestBunnyState({ kind: "walk", frameIdx: 0 });
    expect(service.update(0, CAMERA, walk, false).status).toBe("Exploring together");
    expect(service.update(0.1, { x: -150, z: 0 }, walk, false).status).toBe("Companion is catching up");
    expect(service.update(0.1, { x: -150, z: 0 }, createTestBunnyState({ kind: "jump", frameIdx: 0 }), false).status).toBe("Jumping together");
  });
  it("handles camera reset and depth wrap without throwing the companion offscreen", () => {
    const service = createAdventure(ASSETS, "bunny", { x: 1000, z: 159 }, 160);
    const view = service.update(0.1, { x: 0, z: 1 }, createTestBunnyState({ kind: "walk", frameIdx: 0 }), false);
    expect(view.companion.x).toBe(115);
    expect(view.companion.z).toBe(10);
  });
  it("propagates missing pose and sprint assets with specific errors", () => {
    const badAlert = createAdventure({ ...ASSETS, alertLeft: [] }, "bunny", CAMERA, 160);
    expect(() => badAlert.update(1, CAMERA, createTestBunnyState({ kind: "idle", frameIdx: 0 }), false)).toThrow("RABBIT_ALERT_FRAME");
    const badRun = createAdventure({ ...ASSETS, lionSprint: { left: [], right: [] } }, "lion", CAMERA, 160);
    expect(() => badRun.update(1, CAMERA, createTestBunnyState({ kind: "walk", frameIdx: 0 }), true)).toThrow("RABBIT_SPRINT_FRAME");
  });
});
