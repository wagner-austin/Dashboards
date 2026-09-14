import { describe, expect, it } from "vitest";
import { senseWorld, wrappedDelta } from "./Awareness.js";
import { createCompanion } from "../entities/Companion.js";
import { createTestEntity, createTestLayer } from "../testing/fixtures.js";
const SCENE = { camera: { x: 0, z: 0 }, depthBounds: { minZ: 0, maxZ: 160, range: 160 }, layers: [] };
describe("rabbit perception", () => {
    it("uses the nearest periodic image after arbitrary world travel", () => {
        expect(wrappedDelta(2410, 800)).toBe(10);
        expect(wrappedDelta(-2410, 800)).toBe(-10);
        expect(wrappedDelta(12, 0)).toBe(12);
    });
    it("continues in its facing direction through an empty scene", () => {
        expect(senseWorld(SCENE, null, false)).toStrictEqual({ wait: false, blocked: false, direction: "left" });
        expect(senseWorld(SCENE, createCompanion(), true)).toStrictEqual({ wait: false, blocked: false, direction: "right" });
    });
    it("waits when its companion falls beyond the leash distance", () => {
        expect(senseWorld(SCENE, { ...createCompanion(), x: 250 }, true)).toStrictEqual({ wait: true, blocked: false, direction: "right" });
    });
    it("turns away from a nearby tree on either side", () => {
        const layer = createTestLayer("trees", 0, 9, [createTestEntity(20, 40), createTestEntity(-20, 40)]);
        expect(senseWorld({ ...SCENE, layers: [layer] }, null, true)).toStrictEqual({ wait: false, blocked: true, direction: "left" });
        expect(senseWorld({ ...SCENE, layers: [layer] }, null, false)).toStrictEqual({ wait: false, blocked: true, direction: "right" });
    });
    it("ignores scenery outside its path, static scenery, and ground tiles", () => {
        const layer = createTestLayer("trees", 0, 9, [createTestEntity(20, 100), createTestEntity(-20, 40), createTestEntity(100, 40)]);
        const close = createTestLayer("close", 0, 9, [createTestEntity(20, 40)]);
        const scene = { ...SCENE, layers: [layer, { ...close, config: { ...close.config, tile: true } },
                { ...close, config: { ...close.config, type: "static" } }] };
        expect(senseWorld(scene, null, true)).toStrictEqual({ wait: false, blocked: false, direction: "right" });
    });
});
//# sourceMappingURL=Awareness.test.js.map