/**
 * @vitest-environment jsdom
 * Tests for scene renderer.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderFrame, type RenderState } from "./SceneRenderer.js";
import { createInitialBunnyState, type BunnyFrames } from "../entities/Bunny.js";
import { createInitialTreeState, type TreeSize } from "../entities/Tree.js";
import { createSceneState, type SceneState } from "../layers/index.js";

function createTestBunnyFrames(): BunnyFrames {
  return {
    walkLeft: ["walk_l_0", "walk_l_1"],
    walkRight: ["walk_r_0", "walk_r_1"],
    jumpLeft: ["jump_l_0"],
    jumpRight: ["jump_r_0"],
    idleLeft: ["idle_l_0"],
    idleRight: ["idle_r_0"],
    walkToIdleLeft: ["trans_l_0", "trans_l_1"],
    walkToIdleRight: ["trans_r_0", "trans_r_1"],
  };
}

function createTestTreeSizes(): TreeSize[] {
  return [
    { width: 60, frames: ["tree_60_0"] },
    { width: 120, frames: ["tree_120_0"] },
    { width: 180, frames: ["tree_180_0"] },
  ];
}

function createTestSceneState(): SceneState {
  return createSceneState([]);
}

describe("renderFrame", () => {
  let screen: HTMLPreElement;

  beforeEach(() => {
    screen = document.createElement("pre");
    document.body.appendChild(screen);
  });

  afterEach(() => {
    document.body.removeChild(screen);
  });

  it("renders frame and returns updated state", () => {
    const bunnyState = createInitialBunnyState();
    const treeState = createInitialTreeState(100);
    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      treeState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      groundScrollX: 0,
      lastTime: 0,
    };

    const bunnyFrames = createTestBunnyFrames();
    const treeSizes = createTestTreeSizes();

    const result = renderFrame(
      renderState,
      bunnyFrames,
      treeSizes,
      screen,
      1000,
      100,
      800
    );

    expect(result.lastTime).toBe(1000);
    expect(typeof result.groundScrollX).toBe("number");
    expect(screen.textContent).toBeDefined();
    expect(screen.textContent.length).toBeGreaterThan(0);
  });

  it("updates scroll when bunny is walking", () => {
    const bunnyState = createInitialBunnyState();
    bunnyState.isWalking = true;
    bunnyState.currentAnimation = "walk";
    bunnyState.facingRight = true;

    const treeState = createInitialTreeState(100);
    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      treeState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      groundScrollX: 0,
      lastTime: 0,
    };

    const bunnyFrames = createTestBunnyFrames();
    const treeSizes = createTestTreeSizes();

    // First frame sets lastTime
    renderFrame(renderState, bunnyFrames, treeSizes, screen, 1000, 100, 800);

    // Second frame with time delta
    renderState.lastTime = 1000;
    const result = renderFrame(
      renderState,
      bunnyFrames,
      treeSizes,
      screen,
      2000,
      100,
      800
    );

    // Scroll should have changed
    expect(result.groundScrollX).not.toBe(0);
  });

  it("updates camera when bunny walks left", () => {
    const bunnyState = createInitialBunnyState();
    bunnyState.isWalking = true;
    bunnyState.currentAnimation = "walk";
    bunnyState.facingRight = false; // Walking left

    const treeState = createInitialTreeState(100);
    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      treeState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      groundScrollX: 0,
      lastTime: 1000, // Set previous time so deltaTime > 0
    };

    const bunnyFrames = createTestBunnyFrames();
    const treeSizes = createTestTreeSizes();

    // Frame with time delta - camera should move left (negative)
    const initialCameraX = sceneState.cameraX;
    renderFrame(renderState, bunnyFrames, treeSizes, screen, 2000, 100, 800);

    // Camera should have moved in the negative direction
    expect(sceneState.cameraX).toBeLessThan(initialCameraX);
  });

  it("handles tree transition", () => {
    const bunnyState = createInitialBunnyState();
    const treeState = createInitialTreeState(100);
    treeState.sizeIdx = 1;
    treeState.targetSizeIdx = 2;
    treeState.sizeTransitionProgress = 0.5;
    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      treeState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      groundScrollX: 0,
      lastTime: 0,
    };

    const bunnyFrames = createTestBunnyFrames();
    const treeSizes = createTestTreeSizes();

    // Should not throw during transition
    const result = renderFrame(
      renderState,
      bunnyFrames,
      treeSizes,
      screen,
      1000,
      100,
      800
    );

    expect(result.lastTime).toBe(1000);
  });

  it("handles null transition frames gracefully", () => {
    const bunnyState = createInitialBunnyState();
    const treeState = createInitialTreeState(100);
    treeState.sizeIdx = 0;
    treeState.targetSizeIdx = 1;
    treeState.sizeTransitionProgress = 0.5;
    treeState.frameIdx = 999; // Invalid frame index will cause null
    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      treeState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      groundScrollX: 0,
      lastTime: 0,
    };

    const bunnyFrames = createTestBunnyFrames();
    const treeSizes = createTestTreeSizes();

    // Should not throw even with invalid frame index
    const result = renderFrame(
      renderState,
      bunnyFrames,
      treeSizes,
      screen,
      1000,
      100,
      800
    );

    expect(result.lastTime).toBe(1000);
  });

  it("handles null tree frame gracefully", () => {
    const bunnyState = createInitialBunnyState();
    const treeState = createInitialTreeState(100);
    treeState.sizeIdx = 999; // Invalid size index will cause null
    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      treeState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      groundScrollX: 0,
      lastTime: 0,
    };

    const bunnyFrames = createTestBunnyFrames();
    const treeSizes = createTestTreeSizes();

    // Should not throw even with invalid size index
    const result = renderFrame(
      renderState,
      bunnyFrames,
      treeSizes,
      screen,
      1000,
      100,
      800
    );

    expect(result.lastTime).toBe(1000);
  });

  it("handles first frame with zero lastTime", () => {
    const bunnyState = createInitialBunnyState();
    const treeState = createInitialTreeState(100);
    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      treeState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      groundScrollX: 0,
      lastTime: 0, // First frame
    };

    const bunnyFrames = createTestBunnyFrames();
    const treeSizes = createTestTreeSizes();

    // Should handle first frame gracefully (deltaTime = 0)
    const result = renderFrame(
      renderState,
      bunnyFrames,
      treeSizes,
      screen,
      1000,
      100,
      800
    );

    expect(result.lastTime).toBe(1000);
    expect(result.groundScrollX).toBe(0); // No scroll on first frame
  });
});
