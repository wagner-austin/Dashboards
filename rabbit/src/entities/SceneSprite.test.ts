/**
 * Tests for SceneSprite entity.
 */

import { describe, it, expect } from "vitest";
import { _test_hooks } from "./SceneSprite.js";
import type { FrameSet } from "../types.js";
import { GROUND_TILE } from "../rendering/Ground.js";

const {
  createSceneSpriteState,
  getSceneSpriteFrame,
  calculateSceneSpriteY,
  advanceSceneSpriteFrame,
} = _test_hooks;

function createTestSizes(): FrameSet[] {
  return [
    { width: 30, frames: ["frame30_0\nline2", "frame30_1\nline2"] },
    { width: 50, frames: ["frame50_0\nline2\nline3"] },
    { width: 80, frames: ["frame80_0"] },
  ];
}

describe("createSceneSpriteState", () => {
  it("creates state with initial values", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 100, 1);

    expect(state.spriteName).toBe("tree");
    expect(state.sizes).toBe(sizes);
    expect(state.x).toBe(100);
    expect(state.sizeIdx).toBe(1);
    expect(state.frameIdx).toBe(0);
  });

  it("allows different size indices", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("mountain", sizes, 50, 2);

    expect(state.sizeIdx).toBe(2);
  });
});

describe("getSceneSpriteFrame", () => {
  it("returns frame at current size and frame index", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 0);

    const frame = getSceneSpriteFrame(state);

    expect(frame).not.toBeNull();
    expect(frame?.lines).toEqual(["frame30_0", "line2"]);
    expect(frame?.width).toBe(30);
  });

  it("returns correct frame for different size index", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 1);

    const frame = getSceneSpriteFrame(state);

    expect(frame).not.toBeNull();
    expect(frame?.lines).toEqual(["frame50_0", "line2", "line3"]);
    expect(frame?.width).toBe(50);
  });

  it("returns correct frame after advancing", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 0);
    state.frameIdx = 1;

    const frame = getSceneSpriteFrame(state);

    expect(frame).not.toBeNull();
    expect(frame?.lines).toEqual(["frame30_1", "line2"]);
  });

  it("returns null for invalid size index", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 99);

    const frame = getSceneSpriteFrame(state);

    expect(frame).toBeNull();
  });

  it("returns null for invalid frame index", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 0);
    state.frameIdx = 99;

    const frame = getSceneSpriteFrame(state);

    expect(frame).toBeNull();
  });
});

describe("calculateSceneSpriteY", () => {
  it("positions sprite above ground", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 0);
    const viewportHeight = 24;

    const y = calculateSceneSpriteY(state, viewportHeight);

    // frame30_0 has 2 lines, ground has GROUND_TILE.length rows
    // y = 24 - 6 - 2 = 16
    expect(y).toBe(viewportHeight - GROUND_TILE.length - 2);
  });

  it("accounts for different sprite heights", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 1);
    const viewportHeight = 24;

    const y = calculateSceneSpriteY(state, viewportHeight);

    // frame50_0 has 3 lines
    // y = 24 - 6 - 3 = 15
    expect(y).toBe(viewportHeight - GROUND_TILE.length - 3);
  });

  it("returns ground level for invalid size index", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 99);
    const viewportHeight = 24;

    const y = calculateSceneSpriteY(state, viewportHeight);

    // Falls back to ground level when frame is null
    expect(y).toBe(viewportHeight - GROUND_TILE.length);
  });
});

describe("advanceSceneSpriteFrame", () => {
  it("advances frame index", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 0);

    expect(state.frameIdx).toBe(0);
    advanceSceneSpriteFrame(state);
    expect(state.frameIdx).toBe(1);
  });

  it("wraps frame index to 0 at end", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 0);
    state.frameIdx = 1; // Last frame for size 0

    advanceSceneSpriteFrame(state);

    expect(state.frameIdx).toBe(0);
  });

  it("does nothing for invalid size index", () => {
    const sizes = createTestSizes();
    const state = createSceneSpriteState("tree", sizes, 0, 99);
    state.frameIdx = 5;

    advanceSceneSpriteFrame(state);

    expect(state.frameIdx).toBe(5); // Unchanged
  });
});
