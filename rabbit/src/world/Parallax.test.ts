/**
 * Tests for parallax scrolling calculations.
 */

import { describe, expect, it } from "vitest";
import { calculateScrollUpdate, updateSpeedTransition } from "./Parallax.js";

describe("calculateScrollUpdate", () => {
  const viewportWidth = 100;
  const maxTreeWidth = 180;

  describe("when facing right", () => {
    it("decreases both ground and tree positions", () => {
      const result = calculateScrollUpdate(0, 50, 10, true, viewportWidth, maxTreeWidth);
      expect(result.groundScrollX).toBe(-10);
      expect(result.treeCenterX).toBe(40);
    });

    it("wraps tree to right side when going past left edge", () => {
      const result = calculateScrollUpdate(0, -80, 20, true, viewportWidth, maxTreeWidth);
      // Tree at -80, scroll -20 = -100, which is < -90 (maxTreeWidth/2)
      expect(result.treeCenterX).toBe(viewportWidth + maxTreeWidth / 2);
    });

    it("does not wrap tree when still visible", () => {
      const result = calculateScrollUpdate(0, 0, 10, true, viewportWidth, maxTreeWidth);
      expect(result.treeCenterX).toBe(-10);
    });
  });

  describe("when facing left", () => {
    it("increases both ground and tree positions", () => {
      const result = calculateScrollUpdate(0, 50, 10, false, viewportWidth, maxTreeWidth);
      expect(result.groundScrollX).toBe(10);
      expect(result.treeCenterX).toBe(60);
    });

    it("wraps tree to left side when going past right edge", () => {
      const result = calculateScrollUpdate(0, 180, 20, false, viewportWidth, maxTreeWidth);
      // Tree at 180, scroll +20 = 200, which is > 190 (width + maxTreeWidth/2)
      expect(result.treeCenterX).toBe(-maxTreeWidth / 2);
    });

    it("does not wrap tree when still visible", () => {
      const result = calculateScrollUpdate(0, 100, 10, false, viewportWidth, maxTreeWidth);
      expect(result.treeCenterX).toBe(110);
    });
  });
});

describe("updateSpeedTransition", () => {
  const transitionDurationMs = 800;

  describe("when not transitioning", () => {
    it("returns current size with zero progress", () => {
      const result = updateSpeedTransition(1, 1, 0, 100, transitionDurationMs);
      expect(result.treeSizeIdx).toBe(1);
      expect(result.treeSizeTransitionProgress).toBe(0);
    });

    it("returns correct speed multiplier for size 0", () => {
      const result = updateSpeedTransition(0, 0, 0, 100, transitionDurationMs);
      expect(result.currentSpeedMultiplier).toBe(0.5);
    });

    it("returns correct speed multiplier for size 1", () => {
      const result = updateSpeedTransition(1, 1, 0, 100, transitionDurationMs);
      expect(result.currentSpeedMultiplier).toBe(1.0);
    });

    it("returns correct speed multiplier for size 2", () => {
      const result = updateSpeedTransition(2, 2, 0, 100, transitionDurationMs);
      expect(result.currentSpeedMultiplier).toBe(1.5);
    });

    it("resets progress to zero when not transitioning", () => {
      const result = updateSpeedTransition(1, 1, 0.5, 100, transitionDurationMs);
      expect(result.treeSizeTransitionProgress).toBe(0);
    });
  });

  describe("when transitioning up (smaller to larger)", () => {
    it("increments progress based on delta time", () => {
      // 100ms / 800ms = 0.125
      const result = updateSpeedTransition(1, 2, 0, 100, transitionDurationMs);
      expect(result.treeSizeTransitionProgress).toBe(0.125);
      expect(result.treeSizeIdx).toBe(1);
    });

    it("lerps speed multiplier during transition", () => {
      // At 50% progress from size 1 (1.0) to size 2 (1.5)
      const result = updateSpeedTransition(1, 2, 0.5, 0, transitionDurationMs);
      expect(result.currentSpeedMultiplier).toBe(1.25);
    });

    it("completes transition when progress reaches 1", () => {
      // 0.9 + (400ms / 800ms) = 0.9 + 0.5 = 1.4 >= 1
      const result = updateSpeedTransition(1, 2, 0.9, 400, transitionDurationMs);
      expect(result.treeSizeIdx).toBe(2);
      expect(result.treeSizeTransitionProgress).toBe(0);
      expect(result.currentSpeedMultiplier).toBe(1.5);
    });
  });

  describe("when transitioning down (larger to smaller)", () => {
    it("decrements size index when complete", () => {
      const result = updateSpeedTransition(2, 1, 0.9, 400, transitionDurationMs);
      expect(result.treeSizeIdx).toBe(1);
      expect(result.treeSizeTransitionProgress).toBe(0);
    });

    it("lerps speed multiplier downward during transition", () => {
      // At 50% progress from size 2 (1.5) to size 1 (1.0)
      const result = updateSpeedTransition(2, 1, 0.5, 0, transitionDurationMs);
      expect(result.currentSpeedMultiplier).toBe(1.25);
    });
  });

  describe("multi-step transitions", () => {
    it("handles transition from 0 to 2 in steps", () => {
      // First step: 0 -> 1
      let result = updateSpeedTransition(0, 2, 0.99, 100, transitionDurationMs);
      expect(result.treeSizeIdx).toBe(1);

      // Second step: 1 -> 2
      result = updateSpeedTransition(1, 2, 0.99, 100, transitionDurationMs);
      expect(result.treeSizeIdx).toBe(2);
    });
  });
});
