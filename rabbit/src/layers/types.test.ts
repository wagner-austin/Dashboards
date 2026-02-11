/**
 * Tests for layer types.
 */

import { describe, it, expect } from "vitest";
import { createSceneState, createRenderCandidate, type LayerInstance, type ValidatedLayer, type SceneSpriteState } from "./types.js";
import { createCamera, DEFAULT_CAMERA_Z, type DepthBounds } from "../world/Projection.js";
import { LAYER_BEHAVIORS, type FrameSet } from "../types.js";

/** Test depth bounds (minZ=-110, maxZ=160, range=270) */
function createTestDepthBounds(): DepthBounds {
  return { minZ: -110, maxZ: 160, range: 270 };
}

function createTestLayer(name: string, zIndex: number, layer = 10): ValidatedLayer {
  return {
    name,
    type: "sprites",
    layer,
    spriteNames: [],
    positions: [],
    zIndex,
    tile: false,
    behavior: LAYER_BEHAVIORS.midground,
  };
}

function createTestLayerInstance(name: string, zIndex: number, layer = 10): LayerInstance {
  return {
    config: createTestLayer(name, zIndex, layer),
    entities: [],
  };
}

describe("createSceneState", () => {
  const depthBounds = createTestDepthBounds();

  it("creates scene state with empty layers", () => {
    const camera = createCamera();
    const state = createSceneState([], camera, depthBounds);
    expect(state.layers).toEqual([]);
    expect(state.camera).toEqual({ x: 0, z: DEFAULT_CAMERA_Z });
    expect(state.depthBounds).toEqual(depthBounds);
  });

  it("creates scene state with multiple layers", () => {
    const layers = [
      createTestLayerInstance("sky", 0, 20),
      createTestLayerInstance("foreground", 1, 7),
    ];
    const camera = createCamera();
    const state = createSceneState(layers, camera, depthBounds);
    expect(state.layers.length).toBe(2);
    expect(state.layers[0]?.config.name).toBe("sky");
    expect(state.layers[0]?.config.layer).toBe(20);
    expect(state.layers[1]?.config.name).toBe("foreground");
    expect(state.layers[1]?.config.layer).toBe(7);
    expect(state.camera.x).toBe(0);
    expect(state.camera.z).toBe(DEFAULT_CAMERA_Z);
  });

  it("allows camera to be mutated", () => {
    const camera = createCamera();
    const state = createSceneState([], camera, depthBounds);
    state.camera = { x: 100, z: 75 };
    expect(state.camera.x).toBe(100);
    expect(state.camera.z).toBe(75);
  });

  it("includes layer positions in config", () => {
    const config: ValidatedLayer = {
      name: "forest",
      type: "sprites",
      layer: 7,
      spriteNames: ["tree"],
      positions: [-100, 0, 100, 200],
      zIndex: 0,
      tile: false,
      behavior: LAYER_BEHAVIORS.midground,
    };
    const layer: LayerInstance = { config, entities: [] };
    const state = createSceneState([layer], createCamera(), depthBounds);
    expect(state.layers[0]?.config.positions).toEqual([-100, 0, 100, 200]);
  });
});

function createTestSizes(): FrameSet[] {
  return [{ width: 10, frames: ["ABC\nDEF"] }];
}

function createTestEntity(worldX: number, worldZ: number): SceneSpriteState {
  return {
    spriteName: "test",
    sizes: createTestSizes(),
    sizeIdx: 0,
    frameIdx: 0,
    worldX,
    worldZ,
  };
}

describe("createRenderCandidate", () => {
  it("creates candidate with entity and effectiveZ", () => {
    const entity = createTestEntity(50, 100);
    const candidate = createRenderCandidate(entity, 150);
    expect(candidate.entity).toBe(entity);
    expect(candidate.effectiveZ).toBe(150);
  });

  it("allows effectiveZ different from entity worldZ", () => {
    const entity = createTestEntity(0, 100);
    const candidate = createRenderCandidate(entity, 370);
    expect(candidate.entity.worldZ).toBe(100);
    expect(candidate.effectiveZ).toBe(370);
  });

  it("handles negative effectiveZ", () => {
    const entity = createTestEntity(0, 100);
    const candidate = createRenderCandidate(entity, -170);
    expect(candidate.effectiveZ).toBe(-170);
  });

  it("preserves entity reference", () => {
    const entity = createTestEntity(25, 75);
    const candidate = createRenderCandidate(entity, 75);
    expect(candidate.entity).toBe(entity);
    expect(candidate.entity.worldX).toBe(25);
    expect(candidate.entity.worldZ).toBe(75);
  });
});
