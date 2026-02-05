/**
 * Tests for layer types.
 */

import { describe, it, expect } from "vitest";
import { createSceneState, type LayerInstance, type ValidatedLayer } from "./types.js";

function createTestLayer(name: string, zIndex: number): ValidatedLayer {
  return {
    name,
    type: "sprites",
    parallax: 1.0,
    spriteNames: [],
    zIndex,
    tile: false,
  };
}

function createTestLayerInstance(name: string, zIndex: number): LayerInstance {
  return {
    config: createTestLayer(name, zIndex),
    entities: [],
  };
}

describe("createSceneState", () => {
  it("creates scene state with empty layers", () => {
    const state = createSceneState([]);
    expect(state.layers).toEqual([]);
    expect(state.cameraX).toBe(0);
  });

  it("creates scene state with multiple layers", () => {
    const layers = [
      createTestLayerInstance("sky", 0),
      createTestLayerInstance("foreground", 1),
    ];
    const state = createSceneState(layers);
    expect(state.layers.length).toBe(2);
    expect(state.layers[0]?.config.name).toBe("sky");
    expect(state.layers[1]?.config.name).toBe("foreground");
    expect(state.cameraX).toBe(0);
  });

  it("allows cameraX to be mutated", () => {
    const state = createSceneState([]);
    state.cameraX = 100;
    expect(state.cameraX).toBe(100);
  });
});
