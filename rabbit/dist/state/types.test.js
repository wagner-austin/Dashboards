/**
 * Tests for game state types and functions.
 */
import { describe, expect, it } from "vitest";
import { createInitialState, easeInOut, getSpeedMultiplier, lerp, } from "./types.js";
describe("createInitialState", () => {
    const mockViewport = {
        width: 100,
        height: 50,
        charW: 8,
        charH: 16,
    };
    const mockTreeSizes = [
        { width: 60, frames: ["frame1"] },
        { width: 120, frames: ["frame1", "frame2"] },
        { width: 180, frames: ["frame1", "frame2", "frame3"] },
    ];
    const mockSprites = {
        bunnyWalkFramesLeft: ["walk_left_1"],
        bunnyWalkFramesRight: ["walk_right_1"],
        bunnyJumpFramesLeft: ["jump_left_1"],
        bunnyJumpFramesRight: ["jump_right_1"],
        bunnyIdleFramesLeft: ["idle_left_1"],
        bunnyIdleFramesRight: ["idle_right_1"],
        treeSizes: mockTreeSizes,
    };
    it("creates state with correct viewport", () => {
        const state = createInitialState(mockViewport, mockSprites);
        expect(state.viewport).toEqual(mockViewport);
    });
    it("creates state with default animation values", () => {
        const state = createInitialState(mockViewport, mockSprites);
        expect(state.facingRight).toBe(false);
        expect(state.currentAnimation).toBe("idle");
        expect(state.bunnyFrameIdx).toBe(0);
        expect(state.isJumping).toBe(false);
        expect(state.jumpFrameIdx).toBe(0);
    });
    it("creates state with default walk controls", () => {
        const state = createInitialState(mockViewport, mockSprites);
        expect(state.isWalking).toBe(false);
    });
    it("creates state with default scroll position", () => {
        const state = createInitialState(mockViewport, mockSprites);
        expect(state.groundScrollX).toBe(0);
    });
    it("creates state with default tree animation state", () => {
        const state = createInitialState(mockViewport, mockSprites);
        expect(state.treeFrameIdx).toBe(0);
        expect(state.treeDirection).toBe(1);
        expect(state.treeSizeIdx).toBe(1);
        expect(state.treeTargetSizeIdx).toBe(1);
        expect(state.treeSizeTransitionProgress).toBe(0);
    });
    it("creates state with tree center off-screen right", () => {
        const state = createInitialState(mockViewport, mockSprites);
        expect(state.treeCenterX).toBe(mockViewport.width + 60);
    });
    it("creates state with medium speed multiplier", () => {
        const state = createInitialState(mockViewport, mockSprites);
        expect(state.currentSpeedMultiplier).toBe(1.0);
    });
    it("includes sprite data", () => {
        const state = createInitialState(mockViewport, mockSprites);
        expect(state.bunnyWalkFramesLeft).toEqual(mockSprites.bunnyWalkFramesLeft);
        expect(state.bunnyWalkFramesRight).toEqual(mockSprites.bunnyWalkFramesRight);
        expect(state.bunnyJumpFramesLeft).toEqual(mockSprites.bunnyJumpFramesLeft);
        expect(state.bunnyJumpFramesRight).toEqual(mockSprites.bunnyJumpFramesRight);
        expect(state.bunnyIdleFramesLeft).toEqual(mockSprites.bunnyIdleFramesLeft);
        expect(state.bunnyIdleFramesRight).toEqual(mockSprites.bunnyIdleFramesRight);
        expect(state.treeSizes).toEqual(mockTreeSizes);
    });
});
describe("getSpeedMultiplier", () => {
    it("returns 0.5 for size index 0 (far)", () => {
        expect(getSpeedMultiplier(0)).toBe(0.5);
    });
    it("returns 1.0 for size index 1 (medium)", () => {
        expect(getSpeedMultiplier(1)).toBe(1.0);
    });
    it("returns 1.5 for size index 2 (close)", () => {
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
    it("accelerates in first half (below linear)", () => {
        // At 0.25, easeInOut should be less than 0.25 (ease-in portion)
        expect(easeInOut(0.25)).toBeLessThan(0.25);
    });
    it("decelerates in second half (above linear)", () => {
        // At 0.75, easeInOut should be greater than 0.75 (ease-out portion)
        expect(easeInOut(0.75)).toBeGreaterThan(0.75);
    });
});
describe("lerp", () => {
    it("returns start value at progress 0", () => {
        expect(lerp(10, 20, 0)).toBe(10);
    });
    it("returns end value at progress 1", () => {
        expect(lerp(10, 20, 1)).toBe(20);
    });
    it("returns midpoint at progress 0.5 with easing", () => {
        // With easing, 0.5 still maps to 0.5 (S-curve midpoint)
        expect(lerp(10, 20, 0.5)).toBe(15);
    });
    it("handles negative values", () => {
        expect(lerp(-10, 10, 0.5)).toBe(0);
    });
    it("handles decreasing range", () => {
        expect(lerp(20, 10, 0.5)).toBe(15);
    });
    it("uses linear interpolation when eased is false", () => {
        // At 0.25 linear should be exactly 0.25 of the way
        expect(lerp(0, 100, 0.25, false)).toBe(25);
    });
    it("uses eased interpolation by default", () => {
        // At 0.25 eased should be less than 0.25 of the way
        expect(lerp(0, 100, 0.25)).toBeLessThan(25);
    });
});
//# sourceMappingURL=types.test.js.map