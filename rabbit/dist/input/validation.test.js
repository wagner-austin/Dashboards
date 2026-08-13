/**
 * Tests for autorun configuration decoding.
 */
import { describe, it, expect } from "vitest";
import { _test_hooks } from "./validation.js";
const { isRecord, requireBoolean, requireNumber, validateAutorunConfig, DEFAULT_AUTORUN_CONFIG } = _test_hooks;
describe("isRecord", () => {
    it("accepts plain objects", () => {
        expect(isRecord({})).toBe(true);
        expect(isRecord({ enabled: true })).toBe(true);
    });
    it("rejects null, arrays, and primitives", () => {
        expect(isRecord(null)).toBe(false);
        expect(isRecord([])).toBe(false);
        expect(isRecord("autorun")).toBe(false);
        expect(isRecord(7)).toBe(false);
        expect(isRecord(undefined)).toBe(false);
    });
});
describe("requireBoolean", () => {
    it("returns the fallback when absent", () => {
        expect(requireBoolean(undefined, "enabled", true)).toBe(true);
        expect(requireBoolean(undefined, "enabled", false)).toBe(false);
    });
    it("returns the supplied value when present", () => {
        expect(requireBoolean(false, "enabled", true)).toBe(false);
    });
    it("names the offending field when the type is wrong", () => {
        expect(() => requireBoolean("yes", "enabled", true)).toThrow('autorun: "enabled" must be a boolean');
    });
});
describe("requireNumber", () => {
    it("returns the fallback when absent", () => {
        expect(requireNumber(undefined, "idleDelay", 5, 0, 10)).toBe(5);
    });
    it("returns the supplied value when in range", () => {
        expect(requireNumber(3, "idleDelay", 5, 0, 10)).toBe(3);
    });
    it("accepts both bounds", () => {
        expect(requireNumber(0, "idleDelay", 5, 0, 10)).toBe(0);
        expect(requireNumber(10, "idleDelay", 5, 0, 10)).toBe(10);
    });
    it("rejects non-numbers", () => {
        expect(() => requireNumber("3", "idleDelay", 5, 0, 10)).toThrow('autorun: "idleDelay" must be a number between 0 and 10');
    });
    it("rejects values below the minimum", () => {
        expect(() => requireNumber(-1, "idleDelay", 5, 0, 10)).toThrow('autorun: "idleDelay" must be a number between 0 and 10');
    });
    it("rejects values above the maximum", () => {
        expect(() => requireNumber(11, "idleDelay", 5, 0, 10)).toThrow('autorun: "idleDelay" must be a number between 0 and 10');
    });
    it("rejects non-finite values", () => {
        expect(() => requireNumber(Number.POSITIVE_INFINITY, "idleDelay", 5, 0, 10)).toThrow('autorun: "idleDelay" must be a number between 0 and 10');
        expect(() => requireNumber(Number.NaN, "idleDelay", 5, 0, 10)).toThrow('autorun: "idleDelay" must be a number between 0 and 10');
    });
});
describe("validateAutorunConfig", () => {
    it("returns the defaults when the block is absent", () => {
        expect(validateAutorunConfig(undefined)).toStrictEqual(DEFAULT_AUTORUN_CONFIG);
    });
    it("fills every absent field from the defaults", () => {
        expect(validateAutorunConfig({})).toStrictEqual(DEFAULT_AUTORUN_CONFIG);
    });
    it("accepts a partial block and keeps the rest defaulted", () => {
        const result = validateAutorunConfig({ enabled: false, idleDelay: 12 });
        expect(result.enabled).toBe(false);
        expect(result.idleDelay).toBe(12);
        expect(result.minLeg).toBe(DEFAULT_AUTORUN_CONFIG.minLeg);
        expect(result.jumpChance).toBe(DEFAULT_AUTORUN_CONFIG.jumpChance);
    });
    it("accepts a fully specified block", () => {
        const specified = {
            enabled: true,
            idleDelay: 1,
            minLeg: 2,
            maxLeg: 3,
            minPause: 0.5,
            maxPause: 1.5,
            turnChance: 0.25,
            hopChance: 0.75,
            jumpChance: 1,
        };
        expect(validateAutorunConfig(specified)).toStrictEqual(specified);
    });
    it("rejects a non-object block", () => {
        expect(() => validateAutorunConfig("on")).toThrow("autorun: must be an object");
        expect(() => validateAutorunConfig([])).toThrow("autorun: must be an object");
    });
    it("rejects probabilities outside zero to one", () => {
        expect(() => validateAutorunConfig({ turnChance: 1.5 })).toThrow('autorun: "turnChance" must be a number between 0 and 1');
        expect(() => validateAutorunConfig({ hopChance: -0.1 })).toThrow('autorun: "hopChance" must be a number between 0 and 1');
        expect(() => validateAutorunConfig({ jumpChance: 2 })).toThrow('autorun: "jumpChance" must be a number between 0 and 1');
    });
    it("rejects an inverted leg range", () => {
        expect(() => validateAutorunConfig({ minLeg: 9, maxLeg: 2 })).toThrow('autorun: "minLeg" must not exceed "maxLeg"');
    });
    it("rejects an inverted pause range", () => {
        expect(() => validateAutorunConfig({ minPause: 9, maxPause: 2 })).toThrow('autorun: "minPause" must not exceed "maxPause"');
    });
    it("accepts equal range bounds", () => {
        const result = validateAutorunConfig({ minLeg: 4, maxLeg: 4, minPause: 1, maxPause: 1 });
        expect(result.minLeg).toBe(4);
        expect(result.maxLeg).toBe(4);
        expect(result.minPause).toBe(1);
        expect(result.maxPause).toBe(1);
    });
    it("rejects a non-boolean enabled flag", () => {
        expect(() => validateAutorunConfig({ enabled: 1 })).toThrow('autorun: "enabled" must be a boolean');
    });
});
describe("DEFAULT_AUTORUN_CONFIG", () => {
    it("is enabled with coherent ranges", () => {
        expect(DEFAULT_AUTORUN_CONFIG.enabled).toBe(true);
        expect(DEFAULT_AUTORUN_CONFIG.minLeg).toBeLessThanOrEqual(DEFAULT_AUTORUN_CONFIG.maxLeg);
        expect(DEFAULT_AUTORUN_CONFIG.minPause).toBeLessThanOrEqual(DEFAULT_AUTORUN_CONFIG.maxPause);
    });
});
//# sourceMappingURL=validation.test.js.map