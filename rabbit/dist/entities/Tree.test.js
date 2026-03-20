/**
 * Tests for Tree entity.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createInitialTreeState, createTreeTimer, getTreeFrame, getTreeTransitionFrames, TREE_X_RATIO, } from "./Tree.js";
function createMockSizes() {
    return [
        { width: 60, frames: ["small0", "small1", "small2"] },
        { width: 120, frames: ["med0", "med1", "med2"] },
        { width: 180, frames: ["large0", "large1", "large2", "large3"] },
    ];
}
describe("createInitialTreeState", () => {
    it("initializes tree at configured X ratio", () => {
        const viewportWidth = 300;
        const state = createInitialTreeState(viewportWidth);
        expect(state.worldX).toBe(viewportWidth * TREE_X_RATIO);
    });
    it("starts at second-largest visible size (last is fade-out)", () => {
        // With default 3 sizes: last is fade-out, so starts at max(0, 3-3) = 0
        const state = createInitialTreeState(100);
        expect(state.sizeIdx).toBe(0);
        expect(state.targetSizeIdx).toBe(0);
    });
    it("computes correct initial size with explicit size count", () => {
        // With 9 sizes: second-largest visible = max(0, 9-3) = 6
        const state = createInitialTreeState(100, 9);
        expect(state.sizeIdx).toBe(6);
        expect(state.targetSizeIdx).toBe(6);
    });
    it("starts with no transition in progress", () => {
        const state = createInitialTreeState(100);
        expect(state.sizeTransitionProgress).toBe(0);
    });
    it("initializes with frame index 0 and forward direction", () => {
        const state = createInitialTreeState(100);
        expect(state.frameIdx).toBe(0);
        expect(state.direction).toBe(1);
    });
});
describe("createTreeTimer", () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("advances frame on tick", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 0;
        const sizes = createMockSizes();
        const timer = createTreeTimer(state, sizes, 100);
        timer.start();
        expect(state.frameIdx).toBe(0);
        vi.advanceTimersByTime(100);
        expect(state.frameIdx).toBe(1);
        vi.advanceTimersByTime(100);
        expect(state.frameIdx).toBe(2);
    });
    it("bounces back when reaching end", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 0;
        state.frameIdx = 1;
        state.direction = 1;
        const sizes = createMockSizes();
        const timer = createTreeTimer(state, sizes, 100);
        timer.start();
        vi.advanceTimersByTime(100);
        expect(state.frameIdx).toBe(2);
        vi.advanceTimersByTime(100);
        expect(state.frameIdx).toBe(1);
        expect(state.direction).toBe(-1);
    });
    it("bounces forward when reaching start", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 0;
        state.frameIdx = 1;
        state.direction = -1;
        const sizes = createMockSizes();
        const timer = createTreeTimer(state, sizes, 100);
        timer.start();
        vi.advanceTimersByTime(100);
        expect(state.frameIdx).toBe(0);
        vi.advanceTimersByTime(100);
        expect(state.frameIdx).toBe(1);
        expect(state.direction).toBe(1);
    });
    it("handles undefined size gracefully", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 99;
        const sizes = createMockSizes();
        const timer = createTreeTimer(state, sizes, 100);
        timer.start();
        expect(() => {
            vi.advanceTimersByTime(100);
        }).not.toThrow();
    });
});
describe("getTreeFrame", () => {
    it("returns frame lines and width", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 1;
        state.frameIdx = 0;
        const sizes = createMockSizes();
        const result = getTreeFrame(state, sizes);
        expect(result).not.toBeNull();
        if (result === null) {
            throw new Error("Expected non-null result");
        }
        expect(result.lines).toEqual(["med0"]);
        expect(result.width).toBe(120);
    });
    it("returns null for invalid size index", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 99;
        const sizes = createMockSizes();
        const result = getTreeFrame(state, sizes);
        expect(result).toBeNull();
    });
    it("returns null for invalid frame index", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 0;
        state.frameIdx = 99;
        const sizes = createMockSizes();
        const result = getTreeFrame(state, sizes);
        expect(result).toBeNull();
    });
});
describe("getTreeTransitionFrames", () => {
    it("returns current and next size frames when zooming in", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 0;
        state.targetSizeIdx = 2;
        state.frameIdx = 1;
        const sizes = createMockSizes();
        const result = getTreeTransitionFrames(state, sizes);
        expect(result).not.toBeNull();
        if (result === null) {
            throw new Error("Expected non-null result");
        }
        expect(result.current.lines).toEqual(["small1"]);
        expect(result.current.width).toBe(60);
        expect(result.target.lines).toEqual(["med1"]);
        expect(result.target.width).toBe(120);
        expect(result.targetIdx).toBe(1);
    });
    it("returns current and previous size frames when zooming out", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 2;
        state.targetSizeIdx = 0;
        state.frameIdx = 1;
        const sizes = createMockSizes();
        const result = getTreeTransitionFrames(state, sizes);
        expect(result).not.toBeNull();
        if (result === null) {
            throw new Error("Expected non-null result");
        }
        expect(result.current.lines).toEqual(["large1"]);
        expect(result.target.lines).toEqual(["med1"]);
        expect(result.targetIdx).toBe(1);
    });
    it("wraps frame index for target size", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 2;
        state.targetSizeIdx = 0;
        state.frameIdx = 3;
        const sizes = createMockSizes();
        const result = getTreeTransitionFrames(state, sizes);
        expect(result).not.toBeNull();
        if (result === null) {
            throw new Error("Expected non-null result");
        }
        expect(result.target.lines).toEqual(["med0"]);
    });
    it("returns null for invalid current size", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 99;
        const sizes = createMockSizes();
        const result = getTreeTransitionFrames(state, sizes);
        expect(result).toBeNull();
    });
    it("returns null for invalid computed target size", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 0;
        state.targetSizeIdx = -1;
        const sizes = createMockSizes();
        const result = getTreeTransitionFrames(state, sizes);
        expect(result).toBeNull();
    });
    it("returns null for invalid frame index", () => {
        const state = createInitialTreeState(100);
        state.sizeIdx = 0;
        state.targetSizeIdx = 1;
        state.frameIdx = 99;
        const sizes = createMockSizes();
        const result = getTreeTransitionFrames(state, sizes);
        expect(result).toBeNull();
    });
});
//# sourceMappingURL=Tree.test.js.map