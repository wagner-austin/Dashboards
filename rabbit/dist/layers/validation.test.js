/**
 * Tests for layer validation functions.
 */
import { describe, it, expect } from "vitest";
import { validateLayersConfig, _test_hooks } from "./validation.js";
const { isRecord, isStringArray, isLayerType, requireLayerDefinition, toValidatedLayer } = _test_hooks;
describe("isRecord", () => {
    it("returns true for plain objects", () => {
        expect(isRecord({})).toBe(true);
        expect(isRecord({ key: "value" })).toBe(true);
    });
    it("returns false for null", () => {
        expect(isRecord(null)).toBe(false);
    });
    it("returns false for arrays", () => {
        expect(isRecord([])).toBe(false);
        expect(isRecord([1, 2, 3])).toBe(false);
    });
    it("returns false for primitives", () => {
        expect(isRecord("string")).toBe(false);
        expect(isRecord(123)).toBe(false);
        expect(isRecord(true)).toBe(false);
        expect(isRecord(undefined)).toBe(false);
    });
});
describe("isStringArray", () => {
    it("returns true for empty array", () => {
        expect(isStringArray([])).toBe(true);
    });
    it("returns true for string array", () => {
        expect(isStringArray(["a", "b", "c"])).toBe(true);
    });
    it("returns false for mixed array", () => {
        expect(isStringArray(["a", 1, "c"])).toBe(false);
    });
    it("returns false for non-arrays", () => {
        expect(isStringArray("string")).toBe(false);
        expect(isStringArray({})).toBe(false);
        expect(isStringArray(null)).toBe(false);
    });
});
describe("isLayerType", () => {
    it("returns true for valid layer types", () => {
        expect(isLayerType("static")).toBe(true);
        expect(isLayerType("tile")).toBe(true);
        expect(isLayerType("sprites")).toBe(true);
    });
    it("returns false for invalid layer types", () => {
        expect(isLayerType("invalid")).toBe(false);
        expect(isLayerType("")).toBe(false);
        expect(isLayerType(null)).toBe(false);
        expect(isLayerType(123)).toBe(false);
    });
});
describe("requireLayerDefinition", () => {
    it("validates valid layer definition with all fields", () => {
        const result = requireLayerDefinition({ name: "test", type: "sprites", sprites: ["bunny"], parallax: 0.5 }, 0);
        expect(result.name).toBe("test");
        expect(result.type).toBe("sprites");
        expect(result.sprites).toEqual(["bunny"]);
        expect(result.parallax).toBe(0.5);
    });
    it("validates minimal layer definition", () => {
        const result = requireLayerDefinition({ name: "minimal" }, 0);
        expect(result.name).toBe("minimal");
        expect(result.type).toBeUndefined();
        expect(result.sprites).toBeUndefined();
        expect(result.parallax).toBeUndefined();
    });
    it("throws for non-object", () => {
        expect(() => requireLayerDefinition(null, 0)).toThrow("layers[0]: must be an object");
        expect(() => requireLayerDefinition("string", 1)).toThrow("layers[1]: must be an object");
        expect(() => requireLayerDefinition([], 2)).toThrow("layers[2]: must be an object");
    });
    it("throws for missing name", () => {
        expect(() => requireLayerDefinition({}, 0)).toThrow('layers[0]: missing or invalid "name" field');
        expect(() => requireLayerDefinition({ name: "" }, 0)).toThrow('layers[0]: missing or invalid "name" field');
        expect(() => requireLayerDefinition({ name: 123 }, 0)).toThrow('layers[0]: missing or invalid "name" field');
    });
    it("throws for invalid type", () => {
        expect(() => requireLayerDefinition({ name: "test", type: "invalid" }, 0)).toThrow('layers[0] "test": invalid "type" (must be static|tile|sprites)');
    });
    it("throws for invalid sprites", () => {
        expect(() => requireLayerDefinition({ name: "test", sprites: "not-array" }, 0)).toThrow('layers[0] "test": "sprites" must be string array');
        expect(() => requireLayerDefinition({ name: "test", sprites: [1, 2, 3] }, 0)).toThrow('layers[0] "test": "sprites" must be string array');
    });
    it("throws for invalid parallax", () => {
        expect(() => requireLayerDefinition({ name: "test", parallax: "0.5" }, 0)).toThrow('layers[0] "test": "parallax" must be a number');
    });
    it("throws for invalid tile", () => {
        expect(() => requireLayerDefinition({ name: "test", tile: "yes" }, 0)).toThrow('layers[0] "test": "tile" must be a boolean');
        expect(() => requireLayerDefinition({ name: "test", tile: 1 }, 0)).toThrow('layers[0] "test": "tile" must be a boolean');
    });
    it("validates tile boolean", () => {
        const result = requireLayerDefinition({ name: "test", tile: true }, 0);
        expect(result.tile).toBe(true);
    });
});
describe("toValidatedLayer", () => {
    it("applies defaults for missing optional fields", () => {
        const result = toValidatedLayer({ name: "test" }, 3);
        expect(result.name).toBe("test");
        expect(result.type).toBe("sprites");
        expect(result.parallax).toBe(1.0);
        expect(result.spriteNames).toEqual([]);
        expect(result.zIndex).toBe(3);
        expect(result.tile).toBe(false);
    });
    it("preserves explicit values", () => {
        const result = toValidatedLayer({ name: "sky", type: "static", parallax: 0.0, sprites: ["star"], tile: true }, 0);
        expect(result.name).toBe("sky");
        expect(result.type).toBe("static");
        expect(result.parallax).toBe(0.0);
        expect(result.spriteNames).toEqual(["star"]);
        expect(result.zIndex).toBe(0);
        expect(result.tile).toBe(true);
    });
});
describe("validateLayersConfig", () => {
    it("validates array of layers", () => {
        const result = validateLayersConfig([
            { name: "sky", type: "static", parallax: 0.0 },
            { name: "background", sprites: ["mountain"], parallax: 0.2 },
            { name: "foreground", sprites: ["bunny"], parallax: 1.0 },
        ]);
        expect(result.length).toBe(3);
        expect(result[0]?.name).toBe("sky");
        expect(result[0]?.zIndex).toBe(0);
        expect(result[1]?.name).toBe("background");
        expect(result[1]?.zIndex).toBe(1);
        expect(result[2]?.name).toBe("foreground");
        expect(result[2]?.zIndex).toBe(2);
    });
    it("validates empty array", () => {
        const result = validateLayersConfig([]);
        expect(result).toEqual([]);
    });
    it("throws for non-array", () => {
        expect(() => validateLayersConfig(null)).toThrow("layers: must be an array");
        expect(() => validateLayersConfig({})).toThrow("layers: must be an array");
        expect(() => validateLayersConfig("string")).toThrow("layers: must be an array");
    });
    it("throws for duplicate layer names", () => {
        expect(() => validateLayersConfig([
            { name: "test" },
            { name: "test" },
        ])).toThrow('layers[1]: duplicate layer name "test"');
    });
    it("propagates validation errors from individual layers", () => {
        expect(() => validateLayersConfig([{ invalid: true }])).toThrow('layers[0]: missing or invalid "name" field');
    });
});
//# sourceMappingURL=validation.test.js.map