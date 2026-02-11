/**
 * Tests for layer loading from config.
 */

import { describe, it, expect } from "vitest";
import { _test_hooks } from "./layers.js";
import { LAYER_BEHAVIORS, type Config, type TreeZoomConfig, type LayerSpriteConfig } from "../types.js";
import type { ValidatedLayer } from "../layers/types.js";
import { layerToWorldZ } from "../layers/widths.js";

const { calculateZoomWidths, calculateLayerWidths, getSpriteWidths, createLayerInstances } = _test_hooks;

function createTestConfig(): Config {
  return {
    sprites: {
      bunny: {
        animations: {
          idle: { source: "bunny_idle.gif", widths: [30, 50, 80], contrast: 1.0, invert: false },
          alert: { source: "bunny_alert.gif", widths: [30, 50, 80], contrast: 1.0, invert: false },
        },
      },
      tree: {
        source: "tree.gif",
        widths: [30, 40, 50],
        contrast: 1.0,
        invert: false,
      },
      mountain: {
        source: "mountain.gif",
        widths: [80, 100],
        contrast: 1.0,
        invert: false,
      },
    },
    layers: [],
    settings: { fps: 10, jumpSpeed: 5, scrollSpeed: 10 },
  };
}

describe("calculateZoomWidths", () => {
  it("calculates widths from zoom config", () => {
    const zoom: TreeZoomConfig = {
      horizonY: 0.35,
      foregroundY: 0.95,
      minWidth: 30,
      maxWidth: 180,
      steps: 4,
    };

    const widths = calculateZoomWidths(zoom);

    // steps=4 means 5 widths (0,1,2,3,4)
    expect(widths).toHaveLength(5);
    expect(widths[0]).toBe(30); // minWidth
    expect(widths[4]).toBe(180); // maxWidth
  });

  it("interpolates widths linearly", () => {
    const zoom: TreeZoomConfig = {
      horizonY: 0.3,
      foregroundY: 0.9,
      minWidth: 10,
      maxWidth: 50,
      steps: 2,
    };

    const widths = calculateZoomWidths(zoom);

    // steps=2 means 3 widths: t=0, t=0.5, t=1
    expect(widths).toHaveLength(3);
    expect(widths[0]).toBe(10); // t=0: minWidth
    expect(widths[1]).toBe(30); // t=0.5: round(10 + 40*0.5) = 30
    expect(widths[2]).toBe(50); // t=1: maxWidth
  });

  it("rounds widths to integers", () => {
    const zoom: TreeZoomConfig = {
      horizonY: 0.2,
      foregroundY: 0.8,
      minWidth: 15,
      maxWidth: 320,
      steps: 12,
    };

    const widths = calculateZoomWidths(zoom);

    // All widths should be integers
    for (const width of widths) {
      expect(Number.isInteger(width)).toBe(true);
    }
  });
});

describe("calculateLayerWidths", () => {
  it("generates widths from layer config", () => {
    const layerConfig: LayerSpriteConfig = {
      minWidth: 15,
      maxWidth: 350,
      defaultLayer: 7,
      layerDepth: 14,
    };

    const widths = calculateLayerWidths(layerConfig);

    expect(widths).toHaveLength(14);
    expect(widths[0]).toBe(15);
    expect(widths[widths.length - 1]).toBe(350);
  });

  it("uses power curve for decreasing steps", () => {
    const layerConfig: LayerSpriteConfig = {
      minWidth: 20,
      maxWidth: 200,
      defaultLayer: 5,
      layerDepth: 10,
    };

    const widths = calculateLayerWidths(layerConfig);

    // Gap between first two should be smaller than gap between last two
    const smallGap = (widths[1] ?? 0) - (widths[0] ?? 0);
    const largeGap = (widths[widths.length - 1] ?? 0) - (widths[widths.length - 2] ?? 0);

    expect(largeGap).toBeGreaterThan(smallGap);
  });
});

describe("getSpriteWidths", () => {
  it("returns widths from sprite with direct widths", () => {
    const config = createTestConfig();

    const widths = getSpriteWidths(config, "tree");

    expect(widths).toEqual([30, 40, 50]);
  });

  it("calculates widths from layer config when present", () => {
    const config = createTestConfig();
    config.sprites.treeWithLayer = {
      source: "tree.gif",
      layerConfig: {
        minWidth: 20,
        maxWidth: 100,
        defaultLayer: 7,
        layerDepth: 5,
      },
    };

    const widths = getSpriteWidths(config, "treeWithLayer");

    expect(widths).toHaveLength(5);
    expect(widths[0]).toBe(20);
    expect(widths[4]).toBe(100);
  });

  it("calculates widths from zoom config when present", () => {
    const config = createTestConfig();
    config.sprites.treeWithZoom = {
      source: "tree.gif",
      zoom: {
        horizonY: 0.35,
        foregroundY: 0.95,
        minWidth: 60,
        maxWidth: 180,
        steps: 2,
      },
    };

    const widths = getSpriteWidths(config, "treeWithZoom");

    // steps=2 means 3 widths
    expect(widths).toHaveLength(3);
    expect(widths[0]).toBe(60);
    expect(widths[2]).toBe(180);
  });

  it("prefers explicit widths over layer config", () => {
    const config = createTestConfig();
    config.sprites.mixed = {
      source: "tree.gif",
      widths: [25, 50, 75],
      layerConfig: {
        minWidth: 10,
        maxWidth: 100,
        defaultLayer: 5,
        layerDepth: 10,
      },
    };

    const widths = getSpriteWidths(config, "mixed");

    // Should use explicit widths, not layer config
    expect(widths).toEqual([25, 50, 75]);
  });

  it("returns widths from first animation", () => {
    const config = createTestConfig();

    const widths = getSpriteWidths(config, "bunny");

    expect(widths).toEqual([30, 50, 80]);
  });

  it("returns widths sorted ascending", () => {
    const config = createTestConfig();
    // Modify to have unsorted widths
    config.sprites.tree = { source: "tree.gif", widths: [50, 30, 40], contrast: 1.0, invert: false };

    const widths = getSpriteWidths(config, "tree");

    expect(widths).toEqual([30, 40, 50]);
  });

  it("throws for unknown sprite", () => {
    const config = createTestConfig();

    expect(() => getSpriteWidths(config, "unknown")).toThrow(
      'Sprite "unknown" not found in config'
    );
  });

  it("throws for sprite without widths", () => {
    const config = createTestConfig();
    // Create sprite with no widths at any level
    config.sprites.empty = {} as Config["sprites"][string];

    expect(() => getSpriteWidths(config, "empty")).toThrow(
      'Sprite "empty" has no widths defined'
    );
  });

  it("throws for sprite with empty animations", () => {
    const config = createTestConfig();
    config.sprites.noAnim = { animations: {} } as Config["sprites"][string];

    expect(() => getSpriteWidths(config, "noAnim")).toThrow(
      'Sprite "noAnim" has no widths defined'
    );
  });

  it("throws for sprite with undefined animation value", () => {
    const config = createTestConfig();
    // Animation key exists but value is undefined - creates edge case at line 37
    const animationsWithUndefined = { idle: undefined } as unknown as Record<
      string,
      Config["sprites"][string] extends { animations?: infer A } ? A extends Record<string, infer V> ? V : never : never
    >;
    config.sprites.badAnim = { animations: animationsWithUndefined };

    expect(() => getSpriteWidths(config, "badAnim")).toThrow(
      'Sprite "badAnim" has no widths defined'
    );
  });
});

describe("createLayerInstances", () => {
  it("creates layer instances from validated layers", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "background",
        type: "sprites",
        layer: 15,
        spriteNames: ["tree"],
        positions: [],
        zIndex: 0,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["tree", [{ width: 30, frames: ["T\\n|"] }]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 100);

    expect(instances).toHaveLength(1);
    expect(instances[0]?.config.name).toBe("background");
    expect(instances[0]?.entities).toHaveLength(1);
    expect(instances[0]?.entities[0]?.spriteName).toBe("tree");
  });

  it("creates entities at specified positions", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "forest",
        type: "sprites",
        layer: 7,
        spriteNames: ["tree"],
        positions: [-100, 0, 100, 200],
        zIndex: 0,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["tree", [{ width: 30, frames: ["T"] }]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 100);

    expect(instances[0]?.entities).toHaveLength(4);
    expect(instances[0]?.entities[0]?.worldX).toBe(-100);
    expect(instances[0]?.entities[1]?.worldX).toBe(0);
    expect(instances[0]?.entities[2]?.worldX).toBe(100);
    expect(instances[0]?.entities[3]?.worldX).toBe(200);
  });

  it("converts layer number to worldZ", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "test",
        type: "sprites",
        layer: 10,
        spriteNames: ["tree"],
        positions: [50],
        zIndex: 0,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["tree", [{ width: 30, frames: ["T"] }]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 100);

    const expectedWorldZ = layerToWorldZ(10);
    expect(instances[0]?.entities[0]?.worldZ).toBe(expectedWorldZ);
  });

  it("creates single centered entity when no positions", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "test",
        type: "sprites",
        layer: 10,
        spriteNames: ["tree"],
        positions: [],
        zIndex: 0,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["tree", [{ width: 30, frames: ["T"] }]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 200);

    expect(instances[0]?.entities).toHaveLength(1);
    expect(instances[0]?.entities[0]?.worldX).toBe(100); // Center of viewport
  });

  it("selects middle size index", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "test",
        type: "sprites",
        layer: 10,
        spriteNames: ["tree"],
        positions: [],
        zIndex: 0,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["tree", [
          { width: 30, frames: ["T"] },
          { width: 50, frames: ["TT"] },
          { width: 80, frames: ["TTT"] },
        ]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 100);

    expect(instances[0]?.entities[0]?.sizeIdx).toBe(1); // Middle of 3 sizes
  });

  it("handles multiple sprites in layer", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "foreground",
        type: "sprites",
        layer: 8,
        spriteNames: ["tree", "mountain"],
        positions: [],
        zIndex: 0,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["tree", [{ width: 30, frames: ["T"] }]],
        ["mountain", [{ width: 80, frames: ["M"] }]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 100);

    expect(instances[0]?.entities).toHaveLength(2);
    expect(instances[0]?.entities[0]?.spriteName).toBe("tree");
    expect(instances[0]?.entities[1]?.spriteName).toBe("mountain");
  });

  it("handles multiple layers", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "back",
        type: "sprites",
        layer: 15,
        spriteNames: ["mountain"],
        positions: [],
        zIndex: 0,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
      {
        name: "front",
        type: "sprites",
        layer: 8,
        spriteNames: ["tree"],
        positions: [],
        zIndex: 1,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["tree", [{ width: 30, frames: ["T"] }]],
        ["mountain", [{ width: 80, frames: ["M"] }]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 100);

    expect(instances).toHaveLength(2);
    expect(instances[0]?.config.name).toBe("back");
    expect(instances[1]?.config.name).toBe("front");
  });

  it("throws for sprite not in registry", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "test",
        type: "sprites",
        layer: 10,
        spriteNames: ["unknown"],
        positions: [],
        zIndex: 0,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
    ];

    const registry = {
      sprites: new Map<string, readonly { width: number; frames: string[] }[]>(),
    };

    expect(() => createLayerInstances(layers, registry, 100)).toThrow(
      'Sprite "unknown" not found in registry'
    );
  });

  it("handles empty layers array", () => {
    const layers: ValidatedLayer[] = [];
    const registry = { sprites: new Map() };

    const instances = createLayerInstances(layers, registry, 100);

    expect(instances).toEqual([]);
  });

  it("handles layer with no sprites", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "empty",
        type: "sprites",
        layer: 12,
        spriteNames: [],
        positions: [],
        zIndex: 0,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
    ];

    const registry = { sprites: new Map() };

    const instances = createLayerInstances(layers, registry, 100);

    expect(instances).toHaveLength(1);
    expect(instances[0]?.entities).toEqual([]);
  });

  it("creates multiple entities when tile is true", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "grass",
        type: "sprites",
        layer: 6,
        spriteNames: ["grass"],
        positions: [],
        zIndex: 0,
        tile: true,
        behavior: LAYER_BEHAVIORS.foreground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["grass", [{ width: 50, frames: ["GRASS"] }]],
      ]),
    };

    // Viewport width 100, sprite width 50
    // Total width = 100 + 400 (buffer) = 500
    // numTiles = ceil(500/50) + 1 = 11
    const instances = createLayerInstances(layers, registry, 100);

    expect(instances).toHaveLength(1);
    expect(instances[0]?.entities.length).toBeGreaterThan(1);

    // Entities should be spaced by sprite width
    const entities = instances[0]?.entities;
    if (entities !== undefined && entities.length >= 2) {
      const first = entities[0];
      const second = entities[1];
      if (first !== undefined && second !== undefined) {
        const spacing = second.worldX - first.worldX;
        expect(spacing).toBe(50); // sprite width
      }
    }
  });

  it("uses default width when sizes array is empty", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "empty-sizes",
        type: "sprites",
        layer: 10,
        spriteNames: ["empty"],
        positions: [],
        zIndex: 0,
        tile: true,
        behavior: LAYER_BEHAVIORS.foreground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["empty", []], // Empty sizes array
      ]),
    };

    // Should not throw - uses default width of 100
    const instances = createLayerInstances(layers, registry, 100);
    expect(instances).toHaveLength(1);
    expect(instances[0]?.entities.length).toBeGreaterThan(0);
  });

  it("uses middle size width for tiling calculations", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "tiled",
        type: "sprites",
        layer: 10,
        spriteNames: ["multi"],
        positions: [],
        zIndex: 0,
        tile: true,
        behavior: LAYER_BEHAVIORS.foreground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["multi", [
          { width: 30, frames: ["S"] },
          { width: 60, frames: ["M"] },
          { width: 90, frames: ["L"] },
        ]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 100);
    const entities = instances[0]?.entities;

    // Should use middle size (60) for spacing
    if (entities !== undefined && entities.length >= 2) {
      const first = entities[0];
      const second = entities[1];
      if (first !== undefined && second !== undefined) {
        const spacing = second.worldX - first.worldX;
        expect(spacing).toBe(60);
      }
    }
  });

  it("prefers positions over single centered entity", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "positioned",
        type: "sprites",
        layer: 7,
        spriteNames: ["tree"],
        positions: [0],
        zIndex: 0,
        tile: false,
        behavior: LAYER_BEHAVIORS.midground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["tree", [{ width: 30, frames: ["T"] }]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 200);

    expect(instances[0]?.entities).toHaveLength(1);
    expect(instances[0]?.entities[0]?.worldX).toBe(0); // Position, not centered (100)
  });

  it("tile mode ignores positions", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "tiled",
        type: "sprites",
        layer: 6,
        spriteNames: ["grass"],
        positions: [500, 600, 700], // These should be ignored
        zIndex: 0,
        tile: true,
        behavior: LAYER_BEHAVIORS.foreground,
      },
    ];

    const registry = {
      sprites: new Map([
        ["grass", [{ width: 50, frames: ["G"] }]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 100);

    // Should have tiled entities, not 3 positioned entities
    expect(instances[0]?.entities.length).toBeGreaterThan(3);
  });
});
