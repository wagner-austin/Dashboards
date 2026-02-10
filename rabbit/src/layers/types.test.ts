/**
 * Tests for layer types.
 */

import { describe, it, expect } from "vitest";
import { createSceneState, type LayerInstance, type ValidatedLayer } from "./types.js";
import { createCamera, DEFAULT_CAMERA_Z } from "../world/Projection.js";

function createTestLayer(name: string, zIndex: number, layer = 10): ValidatedLayer {
  return {
    name,
    type: "sprites",
    layer,
    spriteNames: [],
    positions: [],
    zIndex,
    tile: false,
  };
}

function createTestLayerInstance(name: string, zIndex: number, layer = 10): LayerInstance {
  return {
    config: createTestLayer(name, zIndex, layer),
    entities: [],
  };
}

describe("createSceneState", () => {
  it("creates scene state with empty layers", () => {
    const camera = createCamera();
    const state = createSceneState([], camera);
    expect(state.layers).toEqual([]);
    expect(state.camera).toEqual({ x: 0, z: DEFAULT_CAMERA_Z });
  });

  it("creates scene state with multiple layers", () => {
    const layers = [
      createTestLayerInstance("sky", 0, 20),
      createTestLayerInstance("foreground", 1, 7),
    ];
    const camera = createCamera();
    const state = createSceneState(layers, camera);
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
    const state = createSceneState([], camera);
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
    };
    const layer: LayerInstance = { config, entities: [] };
    const state = createSceneState([layer], createCamera());
    expect(state.layers[0]?.config.positions).toEqual([-100, 0, 100, 200]);
  });
});
