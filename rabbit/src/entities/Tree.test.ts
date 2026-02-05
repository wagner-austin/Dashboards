/**
 * Tests for Tree entity.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  createInitialTreeState,
  createTreeTimer,
  calcTreeY,
  getTreeFrame,
  getTreeTransitionFrames,
  type TreeSize,
} from "./Tree.js";

function createMockSizes(): TreeSize[] {
  return [
    { width: 60, frames: ["small0", "small1", "small2"] },
    { width: 120, frames: ["med0", "med1", "med2"] },
    { width: 180, frames: ["large0", "large1", "large2", "large3"] },
  ];
}

describe("createInitialTreeState", () => {
  it("initializes tree positioned at 1/3 viewport width", () => {
    const state = createInitialTreeState(100);
    expect(state.centerX).toBe(33); // Math.floor(100 / 3)
  });

  it("starts at largest size (most zoomed in)", () => {
    const state = createInitialTreeState(100);
    expect(state.sizeIdx).toBe(2);
    expect(state.targetSizeIdx).toBe(2);
  });

  it("starts with no transition in progress", () => {
    const state = createInitialTreeState(100);
    expect(state.sizeTransitionProgress).toBe(0);
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
    // Should bounce: frameIdx = 3 >= 3, so frameIdx = 1, direction = -1
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
    // Should bounce: frameIdx = -1 < 0, so frameIdx = 1, direction = 1
    expect(state.frameIdx).toBe(1);
    expect(state.direction).toBe(1);
  });

  it("handles undefined size gracefully", () => {
    const state = createInitialTreeState(100);
    state.sizeIdx = 99; // Invalid
    const sizes = createMockSizes();
    const timer = createTreeTimer(state, sizes, 100);

    timer.start();
    expect(() => {
      vi.advanceTimersByTime(100);
    }).not.toThrow();
  });
});

describe("calcTreeY", () => {
  it("positions tree above ground", () => {
    const viewportHeight = 30;
    const treeHeight = 20;
    const y = calcTreeY(treeHeight, 0, viewportHeight);
    // Ground is 6 rows, tree ground rows for size 0 is 3
    // y = 30 - 6 - 20 + 3 = 7
    expect(y).toBe(7);
  });

  it("adjusts for different size indices", () => {
    const viewportHeight = 30;
    const treeHeight = 20;

    const y0 = calcTreeY(treeHeight, 0, viewportHeight); // ground rows = 3
    const y1 = calcTreeY(treeHeight, 1, viewportHeight); // ground rows = 6
    const y2 = calcTreeY(treeHeight, 2, viewportHeight); // ground rows = 9

    expect(y1 - y0).toBe(3); // Difference of 3 ground rows
    expect(y2 - y1).toBe(3);
  });

  it("uses default ground rows for unknown size index", () => {
    const y = calcTreeY(20, 99, 30);
    // Default is 6 ground rows
    // y = 30 - 6 - 20 + 6 = 10
    expect(y).toBe(10);
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
    if (result === null) throw new Error("Expected non-null result");
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
    if (result === null) throw new Error("Expected non-null result");
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
    if (result === null) throw new Error("Expected non-null result");
    expect(result.current.lines).toEqual(["large1"]);
    expect(result.target.lines).toEqual(["med1"]);
    expect(result.targetIdx).toBe(1);
  });

  it("wraps frame index for target size", () => {
    const state = createInitialTreeState(100);
    state.sizeIdx = 2;
    state.targetSizeIdx = 0;
    state.frameIdx = 3; // Valid for size 2, but size 1 only has 3 frames
    const sizes = createMockSizes();

    const result = getTreeTransitionFrames(state, sizes);
    expect(result).not.toBeNull();
    if (result === null) throw new Error("Expected non-null result");
    // 3 % 3 = 0
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
    // Set sizeIdx to 0 and targetSizeIdx to -1 so computed targetIdx = -1 (invalid)
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
