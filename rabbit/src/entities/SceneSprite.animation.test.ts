/**
 * @vitest-environment jsdom
 * Tests for scene sprite animation stepping.
 *
 * These exercise the layer animation callback that the render loop drives on
 * its own timer, independently of the bunny's animation state machine.
 */

import { describe, it, expect } from "vitest";
import { advanceAllSceneSpriteFrames, createLayerAnimationCallback } from "./SceneSprite.js";
import type { LayerInstance, SceneSpriteState, ValidatedLayer } from "../layers/types.js";
import { createSceneState } from "../layers/index.js";
import { LAYER_BEHAVIORS } from "../types.js";
import { createCamera, type DepthBounds } from "../world/Projection.js";

/** Test depth bounds (minZ=-110, maxZ=160, range=270) */
function createTestDepthBounds(): DepthBounds {
  return { minZ: -110, maxZ: 160, range: 270 };
}

describe("createLayerAnimationCallback", () => {
  it("returns a callback that advances all scene sprite frames", () => {
    const entity: SceneSpriteState = {
      spriteName: "test",
      sizes: [{ width: 10, frames: ["a", "b", "c"] }],
      sizeIdx: 0,
      frameIdx: 0,
      worldX: 0,
      worldZ: 100,
    };
    const layerConfig: ValidatedLayer = {
      name: "test-layer",
      type: "sprites",
      layer: 10,
      spriteNames: ["test"],
      positions: [],
      zIndex: 0,
      tile: false,
      behavior: LAYER_BEHAVIORS.midground,
    };
    const layer: LayerInstance = {
      config: layerConfig,
      entities: [entity],
    };
    const camera = createCamera();
    const depthBounds = createTestDepthBounds();
    const scene = createSceneState([layer], camera, depthBounds);

    const callback = createLayerAnimationCallback(scene);

    // Initial state
    expect(entity.frameIdx).toBe(0);

    // Call the callback
    callback();

    // Frame should have advanced
    expect(entity.frameIdx).toBe(1);

    // Call again
    callback();
    expect(entity.frameIdx).toBe(2);
  });
});

describe("advanceAllSceneSpriteFrames", () => {
  it("advances frame index for all entities in all layers", () => {
    const entity1: SceneSpriteState = {
      spriteName: "test1",
      sizes: [{ width: 10, frames: ["a", "b", "c"] }],
      sizeIdx: 0,
      frameIdx: 0,
      worldX: 0,
      worldZ: 100,
    };
    const entity2: SceneSpriteState = {
      spriteName: "test2",
      sizes: [{ width: 10, frames: ["x", "y"] }],
      sizeIdx: 0,
      frameIdx: 0,
      worldX: 50,
      worldZ: 100,
    };
    const layerConfig: ValidatedLayer = {
      name: "test-layer",
      type: "sprites",
      layer: 10,
      spriteNames: ["test1", "test2"],
      positions: [],
      zIndex: 0,
      tile: false,
      behavior: LAYER_BEHAVIORS.midground,
    };
    const layer: LayerInstance = {
      config: layerConfig,
      entities: [entity1, entity2],
    };
    const camera = createCamera();
    const depthBounds = createTestDepthBounds();
    const scene = createSceneState([layer], camera, depthBounds);

    // Initial state
    expect(entity1.frameIdx).toBe(0);
    expect(entity2.frameIdx).toBe(0);

    // Advance frames
    advanceAllSceneSpriteFrames(scene);

    // Both entities should have advanced
    expect(entity1.frameIdx).toBe(1);
    expect(entity2.frameIdx).toBe(1);

    // Advance again
    advanceAllSceneSpriteFrames(scene);

    // entity1 has 3 frames, entity2 has 2 frames (wraps to 0)
    expect(entity1.frameIdx).toBe(2);
    expect(entity2.frameIdx).toBe(0);
  });

  it("handles empty scene", () => {
    const camera = createCamera();
    const depthBounds = createTestDepthBounds();
    const scene = createSceneState([], camera, depthBounds);
    // Should not throw
    advanceAllSceneSpriteFrames(scene);
  });

  it("handles layer with no entities", () => {
    const layerConfig: ValidatedLayer = {
      name: "empty-layer",
      type: "sprites",
      layer: 10,
      spriteNames: [],
      positions: [],
      zIndex: 0,
      tile: false,
      behavior: LAYER_BEHAVIORS.midground,
    };
    const layer: LayerInstance = {
      config: layerConfig,
      entities: [],
    };
    const camera = createCamera();
    const depthBounds = createTestDepthBounds();
    const scene = createSceneState([layer], camera, depthBounds);
    // Should not throw
    advanceAllSceneSpriteFrames(scene);
  });
});
