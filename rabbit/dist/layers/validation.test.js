/**
 * Tests for layer validation functions.
 */
import { describe, it, expect } from "vitest";
import { validateLayersConfig, processLayersConfig, _test_hooks } from "./validation.js";
import { LAYER_BEHAVIORS } from "../types.js";
import { WORLD_WIDTH } from "../world/Projection.js";
const { isRecord, isStringArray, isNumberArray, isLayerType, isBehaviorPreset, inferBehavior, requireLayerDefinition, requireAutoLayersConfig, toValidatedLayer, createSeededRandom, getSpriteAtIndex, generateAutoLayers, DEFAULT_LAYER, } = _test_hooks;
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
describe("WORLD_WIDTH", () => {
    it("is 800", () => {
        expect(WORLD_WIDTH).toBe(800);
    });
});
describe("createSeededRandom", () => {
    it("generates consistent values for same seed", () => {
        const random1 = createSeededRandom(42);
        const random2 = createSeededRandom(42);
        expect(random1()).toBe(random2());
        expect(random1()).toBe(random2());
    });
    it("generates different values for different seeds", () => {
        const random1 = createSeededRandom(42);
        const random2 = createSeededRandom(123);
        expect(random1()).not.toBe(random2());
    });
    it("generates values between 0 and 1", () => {
        const random = createSeededRandom(12345);
        for (let i = 0; i < 100; i++) {
            const value = random();
            expect(value).toBeGreaterThanOrEqual(0);
            expect(value).toBeLessThan(1);
        }
    });
});
describe("requireAutoLayersConfig", () => {
    it("validates valid config", () => {
        const config = requireAutoLayersConfig({
            sprites: ["tree1", "tree2"],
            minLayer: 8,
            maxLayer: 20,
        });
        expect(config.sprites).toEqual(["tree1", "tree2"]);
        expect(config.minLayer).toBe(8);
        expect(config.maxLayer).toBe(20);
    });
    it("validates config with optional fields", () => {
        const config = requireAutoLayersConfig({
            sprites: ["tree"],
            minLayer: 5,
            maxLayer: 15,
            treesPerLayer: 3,
            seed: 999,
        });
        expect(config.treesPerLayer).toBe(3);
        expect(config.seed).toBe(999);
    });
    it("throws for non-object", () => {
        expect(() => requireAutoLayersConfig(null)).toThrow("autoLayers: must be an object");
        expect(() => requireAutoLayersConfig("string")).toThrow("autoLayers: must be an object");
    });
    it("throws for empty sprites", () => {
        expect(() => requireAutoLayersConfig({
            sprites: [],
            minLayer: 8,
            maxLayer: 20,
        })).toThrow("autoLayers.sprites: must be non-empty string array");
    });
    it("throws for non-array sprites", () => {
        expect(() => requireAutoLayersConfig({
            sprites: "tree",
            minLayer: 8,
            maxLayer: 20,
        })).toThrow("autoLayers.sprites: must be non-empty string array");
    });
    it("throws for non-integer minLayer", () => {
        expect(() => requireAutoLayersConfig({
            sprites: ["tree"],
            minLayer: 8.5,
            maxLayer: 20,
        })).toThrow("autoLayers.minLayer: must be an integer");
    });
    it("throws for non-integer maxLayer", () => {
        expect(() => requireAutoLayersConfig({
            sprites: ["tree"],
            minLayer: 8,
            maxLayer: "20",
        })).toThrow("autoLayers.maxLayer: must be an integer");
    });
    it("throws when minLayer > maxLayer", () => {
        expect(() => requireAutoLayersConfig({
            sprites: ["tree"],
            minLayer: 20,
            maxLayer: 8,
        })).toThrow("autoLayers: minLayer must be <= maxLayer");
    });
    it("throws for invalid treesPerLayer", () => {
        expect(() => requireAutoLayersConfig({
            sprites: ["tree"],
            minLayer: 8,
            maxLayer: 20,
            treesPerLayer: 0,
        })).toThrow("autoLayers.treesPerLayer: must be a positive integer");
    });
    it("throws for non-integer seed", () => {
        expect(() => requireAutoLayersConfig({
            sprites: ["tree"],
            minLayer: 8,
            maxLayer: 20,
            seed: 1.5,
        })).toThrow("autoLayers.seed: must be an integer");
    });
});
describe("generateAutoLayers", () => {
    it("generates correct number of layers", () => {
        const layers = generateAutoLayers({
            sprites: ["tree1", "tree2"],
            minLayer: 8,
            maxLayer: 12,
        });
        expect(layers.length).toBe(5); // 8, 9, 10, 11, 12
    });
    it("alternates sprites across layers", () => {
        const layers = generateAutoLayers({
            sprites: ["tree1", "tree2"],
            minLayer: 8,
            maxLayer: 11,
        });
        expect(layers[0]?.sprites).toEqual(["tree1"]);
        expect(layers[1]?.sprites).toEqual(["tree2"]);
        expect(layers[2]?.sprites).toEqual(["tree1"]);
        expect(layers[3]?.sprites).toEqual(["tree2"]);
    });
    it("generates correct layer numbers", () => {
        const layers = generateAutoLayers({
            sprites: ["tree"],
            minLayer: 10,
            maxLayer: 12,
        });
        expect(layers[0]?.layer).toBe(10);
        expect(layers[1]?.layer).toBe(11);
        expect(layers[2]?.layer).toBe(12);
    });
    it("generates correct number of positions per layer", () => {
        const layers = generateAutoLayers({
            sprites: ["tree"],
            minLayer: 8,
            maxLayer: 8,
            treesPerLayer: 3,
        });
        expect(layers[0]?.positions?.length).toBe(3);
    });
    it("uses default treesPerLayer of 2", () => {
        const layers = generateAutoLayers({
            sprites: ["tree"],
            minLayer: 8,
            maxLayer: 8,
        });
        expect(layers[0]?.positions?.length).toBe(2);
    });
    it("generates unique layer names", () => {
        const layers = generateAutoLayers({
            sprites: ["tree"],
            minLayer: 8,
            maxLayer: 10,
        });
        expect(layers[0]?.name).toBe("auto-trees-8");
        expect(layers[1]?.name).toBe("auto-trees-9");
        expect(layers[2]?.name).toBe("auto-trees-10");
    });
    it("generates consistent positions with same seed", () => {
        const layers1 = generateAutoLayers({
            sprites: ["tree"],
            minLayer: 8,
            maxLayer: 8,
            seed: 42,
        });
        const layers2 = generateAutoLayers({
            sprites: ["tree"],
            minLayer: 8,
            maxLayer: 8,
            seed: 42,
        });
        expect(layers1[0]?.positions).toEqual(layers2[0]?.positions);
    });
    it("generates different positions with different seeds", () => {
        const layers1 = generateAutoLayers({
            sprites: ["tree"],
            minLayer: 8,
            maxLayer: 8,
            seed: 42,
        });
        const layers2 = generateAutoLayers({
            sprites: ["tree"],
            minLayer: 8,
            maxLayer: 8,
            seed: 123,
        });
        expect(layers1[0]?.positions).not.toEqual(layers2[0]?.positions);
    });
});
describe("processLayersConfig", () => {
    it("processes manual layers only when no autoLayers", () => {
        const result = processLayersConfig([
            { name: "sky", type: "static", layer: 20 },
            { name: "ground", layer: 5 },
        ]);
        expect(result.length).toBe(2);
        expect(result[0]?.name).toBe("sky");
        expect(result[1]?.name).toBe("ground");
    });
    it("generates and combines auto layers with manual layers", () => {
        const result = processLayersConfig([{ name: "sky", type: "static", layer: 25 }], { sprites: ["tree"], minLayer: 8, maxLayer: 10 });
        expect(result.length).toBe(4); // 1 manual + 3 auto
        expect(result.some(l => l.name === "sky")).toBe(true);
        expect(result.some(l => l.name === "auto-trees-8")).toBe(true);
    });
    it("sorts layers by layer number (highest first)", () => {
        const result = processLayersConfig([
            { name: "front", layer: 5 },
            { name: "back", layer: 20 },
            { name: "mid", layer: 10 },
        ]);
        expect(result[0]?.layer).toBe(20);
        expect(result[1]?.layer).toBe(10);
        expect(result[2]?.layer).toBe(5);
    });
    it("handles empty manual layers with autoLayers", () => {
        const result = processLayersConfig([], { sprites: ["tree"], minLayer: 8, maxLayer: 9 });
        expect(result.length).toBe(2);
    });
    it("handles undefined autoLayers", () => {
        const result = processLayersConfig([{ name: "test" }], undefined);
        expect(result.length).toBe(1);
    });
    it("handles non-array layers with autoLayers only", () => {
        const result = processLayersConfig(null, { sprites: ["tree"], minLayer: 8, maxLayer: 9 });
        expect(result.length).toBe(2);
        expect(result[0]?.name).toBe("auto-trees-9");
        expect(result[1]?.name).toBe("auto-trees-8");
    });
    it("handles non-array layers without autoLayers", () => {
        const result = processLayersConfig(null, undefined);
        expect(result.length).toBe(0);
    });
});
describe("isBehaviorPreset", () => {
    it("returns true for valid behavior presets", () => {
        expect(isBehaviorPreset("static")).toBe(true);
        expect(isBehaviorPreset("background")).toBe(true);
        expect(isBehaviorPreset("midground")).toBe(true);
        expect(isBehaviorPreset("foreground")).toBe(true);
    });
    it("returns false for invalid values", () => {
        expect(isBehaviorPreset("invalid")).toBe(false);
        expect(isBehaviorPreset(123)).toBe(false);
        expect(isBehaviorPreset(null)).toBe(false);
        expect(isBehaviorPreset(undefined)).toBe(false);
    });
});
describe("inferBehavior", () => {
    it("uses explicit behavior when provided", () => {
        const def = { name: "test", behavior: "background" };
        expect(inferBehavior(def)).toEqual(LAYER_BEHAVIORS.background);
    });
    it("infers static behavior for static type", () => {
        const def = { name: "test", type: "static" };
        expect(inferBehavior(def)).toEqual(LAYER_BEHAVIORS.static);
    });
    it("infers foreground behavior for tiled layers", () => {
        const def = { name: "test", tile: true };
        expect(inferBehavior(def)).toEqual(LAYER_BEHAVIORS.foreground);
    });
    it("defaults to midground behavior", () => {
        const def = { name: "test" };
        expect(inferBehavior(def)).toEqual(LAYER_BEHAVIORS.midground);
    });
});
describe("getSpriteAtIndex", () => {
    it("returns sprite at valid index", () => {
        expect(getSpriteAtIndex(["a", "b", "c"], 0)).toBe("a");
        expect(getSpriteAtIndex(["a", "b", "c"], 1)).toBe("b");
        expect(getSpriteAtIndex(["a", "b", "c"], 2)).toBe("c");
    });
    it("wraps index for cycling", () => {
        expect(getSpriteAtIndex(["a", "b"], 2)).toBe("a");
        expect(getSpriteAtIndex(["a", "b"], 3)).toBe("b");
        expect(getSpriteAtIndex(["a", "b"], 4)).toBe("a");
    });
    it("throws for empty sprites array", () => {
        expect(() => getSpriteAtIndex([], 0)).toThrow("autoLayers: sprites array is empty");
    });
    it("throws for sparse array with undefined hole", () => {
        // Create a sparse array with a hole at index 0
        // This tests the defensive undefined check
        const sparse = [];
        sparse.length = 2;
        sparse[1] = "second";
        expect(() => getSpriteAtIndex(sparse, 0)).toThrow("autoLayers: sprite index 0 out of bounds");
    });
});
describe("requireLayerDefinition with behavior", () => {
    it("accepts valid behavior preset", () => {
        const def = requireLayerDefinition({ name: "test", behavior: "static" }, 0);
        expect(def.behavior).toBe("static");
    });
    it("throws for invalid behavior preset", () => {
        expect(() => requireLayerDefinition({ name: "test", behavior: "invalid" }, 0)).toThrow('"behavior" must be static|background|midground|foreground');
    });
});
//# sourceMappingURL=validation.test.js.map