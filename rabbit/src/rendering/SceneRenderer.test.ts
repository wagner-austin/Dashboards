/**
 * @vitest-environment jsdom
 * Tests for scene renderer.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderFrame, _test_hooks, type RenderState } from "./SceneRenderer.js";

const { drawBunny } = _test_hooks;
import { createInitialBunnyState, type BunnyFrames, type BunnyState, type AnimationState } from "../entities/Bunny.js";
import { createSceneState, type SceneState } from "../layers/index.js";
import { createCamera, createProjectionConfig } from "../world/Projection.js";

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
    walkToTurnAwayLeft: ["turn_away_l_0", "turn_away_l_1"],
    walkToTurnAwayRight: ["turn_away_r_0", "turn_away_r_1"],
    walkToTurnTowardLeft: ["turn_toward_l_0", "turn_toward_l_1"],
    walkToTurnTowardRight: ["turn_toward_r_0", "turn_toward_r_1"],
    hopAway: ["hop_away_0", "hop_away_1"],
    hopToward: ["hop_toward_0", "hop_toward_1"],
  };
}

function createTestBunnyState(animation: AnimationState, facingRight = false): BunnyState {
  return { facingRight, animation };
}

function createTestSceneState(): SceneState {
  return createSceneState([], createCamera());
}

describe("renderFrame", () => {
  let screen: HTMLPreElement;
  const projectionConfig = createProjectionConfig();

  beforeEach(() => {
    screen = document.createElement("pre");
    document.body.appendChild(screen);
  });

  afterEach(() => {
    document.body.removeChild(screen);
  });

  it("renders frame and returns updated state", () => {
    const bunnyState = createInitialBunnyState();
    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      lastTime: 0,
      projectionConfig,
    };

    const bunnyFrames = createTestBunnyFrames();

    const result = renderFrame(
      renderState,
      bunnyFrames,
      screen,
      1000,
      100
    );

    expect(result.lastTime).toBe(1000);
    expect(screen.textContent).not.toBe("");
    expect(screen.textContent.length).toBeGreaterThan(0);
  });

  it("updates camera when bunny is walking right", () => {
    const bunnyState = createTestBunnyState({ kind: "walk", frameIdx: 0 }, true);

    const sceneState = createTestSceneState();
    const initialCameraX = sceneState.camera.x;

    const renderState: RenderState = {
      bunnyState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      lastTime: 1000,
      projectionConfig,
    };

    const bunnyFrames = createTestBunnyFrames();

    renderFrame(renderState, bunnyFrames, screen, 2000, 100);

    expect(sceneState.camera.x).toBeGreaterThan(initialCameraX);
  });

  it("updates camera when bunny walks left", () => {
    const bunnyState = createTestBunnyState({ kind: "walk", frameIdx: 0 }, false);

    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      lastTime: 1000,
      projectionConfig,
    };

    const bunnyFrames = createTestBunnyFrames();

    const initialCameraX = sceneState.camera.x;
    renderFrame(renderState, bunnyFrames, screen, 2000, 100);

    expect(sceneState.camera.x).toBeLessThan(initialCameraX);
  });

  it("handles first frame with zero lastTime", () => {
    const bunnyState = createInitialBunnyState();
    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      lastTime: 0,
      projectionConfig,
    };

    const bunnyFrames = createTestBunnyFrames();

    const result = renderFrame(
      renderState,
      bunnyFrames,
      screen,
      1000,
      100
    );

    expect(result.lastTime).toBe(1000);
  });

  it("does not update camera when bunny is idle", () => {
    const bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });

    const sceneState = createTestSceneState();
    const initialCameraX = sceneState.camera.x;

    const renderState: RenderState = {
      bunnyState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      lastTime: 1000,
      projectionConfig,
    };

    const bunnyFrames = createTestBunnyFrames();

    renderFrame(renderState, bunnyFrames, screen, 2000, 100);

    expect(sceneState.camera.x).toBe(initialCameraX);
  });

  it("does not update camera when bunny is jumping", () => {
    const bunnyState = createTestBunnyState({ kind: "jump", frameIdx: 0, returnTo: "walk" });

    const sceneState = createTestSceneState();
    const initialCameraX = sceneState.camera.x;

    const renderState: RenderState = {
      bunnyState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      lastTime: 1000,
      projectionConfig,
    };

    const bunnyFrames = createTestBunnyFrames();

    renderFrame(renderState, bunnyFrames, screen, 2000, 100);

    expect(sceneState.camera.x).toBe(initialCameraX);
  });

  it("does not update camera when in transition", () => {
    const bunnyState = createTestBunnyState({ kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" });

    const sceneState = createTestSceneState();
    const initialCameraX = sceneState.camera.x;

    const renderState: RenderState = {
      bunnyState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      lastTime: 1000,
      projectionConfig,
    };

    const bunnyFrames = createTestBunnyFrames();

    renderFrame(renderState, bunnyFrames, screen, 2000, 100);

    expect(sceneState.camera.x).toBe(initialCameraX);
  });

  it("renders with scene layers", () => {
    const bunnyState = createInitialBunnyState();
    const sceneState = createTestSceneState();

    const renderState: RenderState = {
      bunnyState,
      sceneState,
      viewport: { width: 80, height: 24, charW: 10, charH: 20 },
      lastTime: 0,
      projectionConfig,
    };

    const bunnyFrames = createTestBunnyFrames();

    const result = renderFrame(
      renderState,
      bunnyFrames,
      screen,
      1000,
      100
    );

    expect(result.lastTime).toBe(1000);
    expect(screen.textContent).not.toBe("");
    expect(screen.textContent.length).toBeGreaterThan(0);
  });
});

describe("drawBunny", () => {
  function createBuffer(width: number, height: number): string[][] {
    return Array.from({ length: height }, () =>
      Array.from({ length: width }, () => " ")
    );
  }

  it("draws bunny to buffer", () => {
    const buffer = createBuffer(80, 24);
    const bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 }, true);
    const bunnyFrames = createTestBunnyFrames();

    drawBunny(buffer, bunnyState, bunnyFrames, 80, 24);

    // Check that bunny was drawn (has non-space content)
    const hasContent = buffer.some((row) => row.some((char) => char !== " "));
    expect(hasContent).toBe(true);
  });

  it("draws bunny facing left", () => {
    const buffer = createBuffer(80, 24);
    const bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 }, false);
    const bunnyFrames = createTestBunnyFrames();

    drawBunny(buffer, bunnyState, bunnyFrames, 80, 24);

    const hasContent = buffer.some((row) => row.some((char) => char !== " "));
    expect(hasContent).toBe(true);
  });
});
