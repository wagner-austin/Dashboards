/**
 * Tests for generic entity transition system.
 */
import { describe, it, expect } from "vitest";
import { createTransitionState, updateSizeTransition, updateVisibilityFade, shouldDrawEntity, isTransitioning, isEntityInForeground, _test_hooks, } from "./EntityTransition.js";
describe("createTransitionState", () => {
    it("creates state with given size index", () => {
        const state = createTransitionState(5);
        expect(state.sizeIdx).toBe(5);
        expect(state.targetSizeIdx).toBe(5);
        expect(state.sizeTransitionProgress).toBe(0);
        expect(state.sizeTransitionDirection).toBe(0);
        expect(state.visibilityProgress).toBe(1);
    });
    it("creates fully visible state", () => {
        const state = createTransitionState(0);
        expect(state.visibilityProgress).toBe(1);
    });
});
describe("updateSizeTransition", () => {
    it("returns false when not transitioning", () => {
        const state = createTransitionState(1);
        const result = updateSizeTransition(state, 100, 800);
        expect(result).toBe(false);
        expect(state.sizeTransitionProgress).toBe(0);
        expect(state.sizeTransitionDirection).toBe(0);
    });
    it("increments progress during transition", () => {
        const state = createTransitionState(1);
        state.targetSizeIdx = 2;
        const result = updateSizeTransition(state, 400, 800);
        expect(result).toBe(true);
        expect(state.sizeTransitionProgress).toBe(0.5);
        expect(state.sizeTransitionDirection).toBe(1);
    });
    it("increments sizeIdx when transition completes going up", () => {
        const state = createTransitionState(1);
        state.targetSizeIdx = 2;
        state.sizeTransitionProgress = 0.9;
        state.sizeTransitionDirection = 1;
        updateSizeTransition(state, 200, 800);
        expect(state.sizeIdx).toBe(2);
        expect(state.sizeTransitionProgress).toBe(0);
    });
    it("decrements sizeIdx when transition completes going down", () => {
        const state = createTransitionState(2);
        state.targetSizeIdx = 1;
        state.sizeTransitionProgress = 0.9;
        state.sizeTransitionDirection = -1;
        updateSizeTransition(state, 200, 800);
        expect(state.sizeIdx).toBe(1);
        expect(state.sizeTransitionProgress).toBe(0);
    });
    it("reverses progress when direction changes mid-transition", () => {
        const state = createTransitionState(5);
        state.targetSizeIdx = 4;
        state.sizeTransitionProgress = 0.3;
        state.sizeTransitionDirection = -1;
        // Now change direction to growing
        state.targetSizeIdx = 6;
        updateSizeTransition(state, 0, 800);
        // Progress should be reversed: 1 - 0.3 = 0.7
        expect(state.sizeTransitionProgress).toBe(0.7);
        expect(state.sizeTransitionDirection).toBe(1);
    });
    it("handles rapid direction changes", () => {
        const state = createTransitionState(5);
        state.targetSizeIdx = 6;
        state.sizeTransitionProgress = 0.2;
        state.sizeTransitionDirection = 1;
        // Change to shrinking
        state.targetSizeIdx = 4;
        updateSizeTransition(state, 100, 800);
        expect(state.sizeTransitionDirection).toBe(-1);
        // Progress reversed then incremented
        expect(state.sizeTransitionProgress).toBeCloseTo(0.8 + 0.125, 5);
    });
});
describe("updateVisibilityFade", () => {
    it("fades out when becoming invisible", () => {
        const state = createTransitionState(0);
        state.visibilityProgress = 1;
        updateVisibilityFade(state, false, 150, 300);
        expect(state.visibilityProgress).toBe(0.5);
    });
    it("fades in when becoming visible", () => {
        const state = createTransitionState(0);
        state.visibilityProgress = 0;
        updateVisibilityFade(state, true, 150, 300);
        expect(state.visibilityProgress).toBe(0.5);
    });
    it("clamps visibility to 0", () => {
        const state = createTransitionState(0);
        state.visibilityProgress = 0.1;
        updateVisibilityFade(state, false, 500, 300);
        expect(state.visibilityProgress).toBe(0);
    });
    it("clamps visibility to 1", () => {
        const state = createTransitionState(0);
        state.visibilityProgress = 0.9;
        updateVisibilityFade(state, true, 500, 300);
        expect(state.visibilityProgress).toBe(1);
    });
});
describe("shouldDrawEntity", () => {
    it("returns true when fully visible", () => {
        const state = createTransitionState(0);
        state.visibilityProgress = 1;
        expect(shouldDrawEntity(state)).toBe(true);
    });
    it("returns true when partially visible", () => {
        const state = createTransitionState(0);
        state.visibilityProgress = 0.5;
        expect(shouldDrawEntity(state)).toBe(true);
    });
    it("returns false when fully invisible", () => {
        const state = createTransitionState(0);
        state.visibilityProgress = 0;
        expect(shouldDrawEntity(state)).toBe(false);
    });
});
describe("isTransitioning", () => {
    it("returns false when at target", () => {
        const state = createTransitionState(2);
        expect(isTransitioning(state)).toBe(false);
    });
    it("returns true when target differs", () => {
        const state = createTransitionState(2);
        state.targetSizeIdx = 3;
        expect(isTransitioning(state)).toBe(true);
    });
    it("returns true when progress is non-zero", () => {
        const state = createTransitionState(2);
        state.sizeTransitionProgress = 0.5;
        expect(isTransitioning(state)).toBe(true);
    });
});
describe("isEntityInForeground", () => {
    it("returns false when sizeCount is zero", () => {
        const state = createTransitionState(0);
        expect(isEntityInForeground(state, 0)).toBe(false);
    });
    it("returns false when not at max size", () => {
        const state = createTransitionState(5);
        state.targetSizeIdx = 5;
        expect(isEntityInForeground(state, 10)).toBe(false);
    });
    it("returns true when at max size", () => {
        const state = createTransitionState(9);
        state.targetSizeIdx = 9;
        expect(isEntityInForeground(state, 10)).toBe(true);
    });
    it("returns true when at second-to-max size", () => {
        const state = createTransitionState(8);
        state.targetSizeIdx = 8;
        // Foreground includes top 2 sizes (8 and 9 when sizeCount=10)
        expect(isEntityInForeground(state, 10)).toBe(true);
    });
    it("returns true when transitioning between top two sizes", () => {
        const state = createTransitionState(8);
        state.targetSizeIdx = 9;
        state.sizeTransitionProgress = 0.5;
        // Both top sizes are foreground
        expect(isEntityInForeground(state, 10)).toBe(true);
    });
    it("returns false when only one size exists", () => {
        const state = createTransitionState(0);
        state.targetSizeIdx = 0;
        // Need at least 2 sizes for foreground logic
        expect(isEntityInForeground(state, 1)).toBe(false);
    });
});
describe("_test_hooks", () => {
    it("exports all functions", () => {
        expect(_test_hooks.createTransitionState).toBe(createTransitionState);
        expect(_test_hooks.updateSizeTransition).toBe(updateSizeTransition);
        expect(_test_hooks.updateVisibilityFade).toBe(updateVisibilityFade);
        expect(_test_hooks.shouldDrawEntity).toBe(shouldDrawEntity);
        expect(_test_hooks.isTransitioning).toBe(isTransitioning);
        expect(_test_hooks.isEntityInForeground).toBe(isEntityInForeground);
    });
});
//# sourceMappingURL=EntityTransition.test.js.map