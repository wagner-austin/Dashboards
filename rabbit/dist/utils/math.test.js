/**
 * Tests for math utilities.
 */
import { describe, it, expect } from "vitest";
import { getSpeedMultiplier, easeInOut, lerp } from "./math.js";
describe("getSpeedMultiplier", () => {
    it("returns 0.5 for size index 0", () => {
        expect(getSpeedMultiplier(0)).toBe(0.5);
    });
    it("returns 1.0 for size index 1", () => {
        expect(getSpeedMultiplier(1)).toBe(1.0);
    });
    it("returns 1.5 for size index 2", () => {
        expect(getSpeedMultiplier(2)).toBe(1.5);
    });
});
describe("easeInOut", () => {
    it("returns 0 at progress 0", () => {
        expect(easeInOut(0)).toBe(0);
    });
    it("returns 1 at progress 1", () => {
        expect(easeInOut(1)).toBe(1);
    });
    it("returns 0.5 at progress 0.5", () => {
        expect(easeInOut(0.5)).toBe(0.5);
    });
    it("applies ease-in for first half", () => {
        const result = easeInOut(0.25);
        expect(result).toBeLessThan(0.25); // Slower start
    });
    it("applies ease-out for second half", () => {
        const result = easeInOut(0.75);
        expect(result).toBeGreaterThan(0.75); // Slower end
    });
});
describe("lerp", () => {
    it("returns start value at progress 0", () => {
        expect(lerp(10, 20, 0)).toBe(10);
    });
    it("returns end value at progress 1", () => {
        expect(lerp(10, 20, 1)).toBe(20);
    });
    it("interpolates with easing by default", () => {
        const result = lerp(0, 100, 0.5);
        expect(result).toBe(50); // easeInOut(0.5) = 0.5
    });
    it("interpolates linearly when eased is false", () => {
        const result = lerp(0, 100, 0.25, false);
        expect(result).toBe(25); // Linear, no easing
    });
    it("applies easing when eased is true", () => {
        const linear = lerp(0, 100, 0.25, false);
        const eased = lerp(0, 100, 0.25, true);
        expect(eased).not.toBe(linear);
        expect(eased).toBeLessThan(linear); // Ease-in starts slower
    });
});
//# sourceMappingURL=math.test.js.map