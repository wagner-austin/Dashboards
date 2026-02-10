/**
 * Tests for layer validation functions.
 */
import { describe, it, expect } from "vitest";
import { validateLayersConfig, _test_hooks } from "./validation.js";
const { isRecord, isStringArray, isNumberArray, isLayerType, requireLayerDefinition, toValidatedLayer, DEFAULT_LAYER, } = _test_hooks;
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
describe("isNumberArray", () => {
    it("returns true for empty array", () => {
        expect(isNumberArray([])).toBe(true);
    });
    it("returns true for number array", () => {
        expect(isNumberArray([1, 2, 3])).toBe(true);
        expect(isNumberArray([-100, 0, 100, 200])).toBe(true);
        expect(isNumberArray([1.5, 2.7, 3.9])).toBe(true);
    });
    it("returns false for mixed array", () => {
        expect(isNumberArray([1, "two", 3])).toBe(false);
    });
    it("returns false for string array", () => {
        expect(isNumberArray(["1", "2", "3"])).toBe(false);
    });
    it("returns false for non-arrays", () => {
        expect(isNumberArray("string")).toBe(false);
        expect(isNumberArray({})).toBe(false);
        expect(isNumberArray(null)).toBe(false);
        expect(isNumberArray(123)).toBe(false);
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
        const result = requireLayerDefinition({ name: "test", type: "sprites", sprites: ["bunny"], positions: [-100, 0, 100], layer: 7 }, 0);
        expect(result.name).toBe("test");
        expect(result.type).toBe("sprites");
        expect(result.sprites).toEqual(["bunny"]);
        expect(result.positions).toEqual([-100, 0, 100]);
        expect(result.layer).toBe(7);
    });
    it("validates minimal layer definition", () => {
        const result = requireLayerDefinition({ name: "minimal" }, 0);
        expect(result.name).toBe("minimal");
        expect(result.type).toBeUndefined();
        expect(result.sprites).toBeUndefined();
        expect(result.positions).toBeUndefined();
        expect(result.layer).toBeUndefined();
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
    it("throws for invalid positions", () => {
        expect(() => requireLayerDefinition({ name: "test", positions: "not-array" }, 0)).toThrow('layers[0] "test": "positions" must be number array');
        expect(() => requireLayerDefinition({ name: "test", positions: ["a", "b"] }, 0)).toThrow('layers[0] "test": "positions" must be number array');
    });
    it("throws for invalid layer", () => {
        expect(() => requireLayerDefinition({ name: "test", layer: "10" }, 0)).toThrow('layers[0] "test": "layer" must be a number');
    });
    it("throws for invalid tile", () => {
        expect(() => requireLayerDefinition({ name: "test", tile: "yes" }, 0)).toThrow('layers[0] "test": "tile" must be a boolean');
        expect(() => requireLayerDefinition({ name: "test", tile: 1 }, 0)).toThrow('layers[0] "test": "tile" must be a boolean');
    });
    it("validates tile boolean", () => {
        const result = requireLayerDefinition({ name: "test", tile: true }, 0);
        expect(result.tile).toBe(true);
    });
    it("validates negative positions", () => {
        const result = requireLayerDefinition({ name: "test", positions: [-200, -100, 0] }, 0);
        expect(result.positions).toEqual([-200, -100, 0]);
    });
    it("validates zero layer", () => {
        const result = requireLayerDefinition({ name: "test", layer: 0 }, 0);
        expect(result.layer).toBe(0);
    });
    it("validates negative layer", () => {
        const result = requireLayerDefinition({ name: "test", layer: -5 }, 0);
        expect(result.layer).toBe(-5);
    });
});
describe("toValidatedLayer", () => {
    it("applies defaults for missing optional fields", () => {
        const result = toValidatedLayer({ name: "test" }, 3);
        expect(result.name).toBe("test");
        expect(result.type).toBe("sprites");
        expect(result.layer).toBe(DEFAULT_LAYER);
        expect(result.spriteNames).toEqual([]);
        expect(result.positions).toEqual([]);
        expect(result.zIndex).toBe(3);
        expect(result.tile).toBe(false);
    });
    it("preserves explicit values", () => {
        const result = toValidatedLayer({ name: "sky", type: "static", layer: 15, sprites: ["star"], positions: [-50, 50], tile: true }, 0);
        expect(result.name).toBe("sky");
        expect(result.type).toBe("static");
        expect(result.layer).toBe(15);
        expect(result.spriteNames).toEqual(["star"]);
        expect(result.positions).toEqual([-50, 50]);
        expect(result.zIndex).toBe(0);
        expect(result.tile).toBe(true);
    });
    it("preserves layer 0", () => {
        const result = toValidatedLayer({ name: "close", layer: 0 }, 0);
        expect(result.layer).toBe(0);
    });
    it("preserves negative layer", () => {
        const result = toValidatedLayer({ name: "veryclose", layer: -2 }, 0);
        expect(result.layer).toBe(-2);
    });
});
describe("validateLayersConfig", () => {
    it("validates array of layers", () => {
        const result = validateLayersConfig([
            { name: "sky", type: "static", layer: 20 },
            { name: "background", sprites: ["mountain"], layer: 15 },
            { name: "foreground", sprites: ["tree"], layer: 7, positions: [-100, 100] },
        ]);
        expect(result.length).toBe(3);
        expect(result[0]?.name).toBe("sky");
        expect(result[0]?.layer).toBe(20);
        expect(result[0]?.zIndex).toBe(0);
        expect(result[1]?.name).toBe("background");
        expect(result[1]?.layer).toBe(15);
        expect(result[1]?.zIndex).toBe(1);
        expect(result[2]?.name).toBe("foreground");
        expect(result[2]?.layer).toBe(7);
        expect(result[2]?.positions).toEqual([-100, 100]);
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
    it("applies default layer when not specified", () => {
        const result = validateLayersConfig([{ name: "test" }]);
        expect(result[0]?.layer).toBe(DEFAULT_LAYER);
    });
});
describe("DEFAULT_LAYER", () => {
    it("is 10", () => {
        expect(DEFAULT_LAYER).toBe(10);
    });
});
//# sourceMappingURL=validation.test.js.map