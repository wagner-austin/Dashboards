/**
 * Tests for layer loading from config.
 */

import { describe, it, expect } from "vitest";
import { _test_hooks } from "./layers.js";
import type { Config } from "../types.js";
import type { ValidatedLayer } from "../layers/types.js";

const { getSpriteWidths, createLayerInstances } = _test_hooks;

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

describe("getSpriteWidths", () => {
  it("returns widths from sprite with direct widths", () => {
    const config = createTestConfig();

    const widths = getSpriteWidths(config, "tree");

    expect(widths).toEqual([30, 40, 50]);
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
        parallax: 0.2,
        spriteNames: ["tree"],
        zIndex: 0,
        tile: false,
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

  it("creates entities centered in viewport", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "test",
        type: "sprites",
        parallax: 1.0,
        spriteNames: ["tree"],
        zIndex: 0,
        tile: false,
      },
    ];

    const registry = {
      sprites: new Map([
        ["tree", [{ width: 30, frames: ["T"] }]],
      ]),
    };

    const instances = createLayerInstances(layers, registry, 200);

    expect(instances[0]?.entities[0]?.x).toBe(100); // Center of viewport
  });

  it("selects middle size index", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "test",
        type: "sprites",
        parallax: 1.0,
        spriteNames: ["tree"],
        zIndex: 0,
        tile: false,
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
        parallax: 1.0,
        spriteNames: ["tree", "mountain"],
        zIndex: 0,
        tile: false,
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
        parallax: 0.2,
        spriteNames: ["mountain"],
        zIndex: 0,
        tile: false,
      },
      {
        name: "front",
        type: "sprites",
        parallax: 1.0,
        spriteNames: ["tree"],
        zIndex: 1,
        tile: false,
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
        parallax: 1.0,
        spriteNames: ["unknown"],
        zIndex: 0,
        tile: false,
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
        parallax: 0.5,
        spriteNames: [],
        zIndex: 0,
        tile: false,
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
        parallax: 1.0,
        spriteNames: ["grass"],
        zIndex: 0,
        tile: true,
      },
    ];

    const registry = {
      sprites: new Map([
        ["grass", [{ width: 50, frames: ["GRASS"] }]],
      ]),
    };

    // Viewport width 100, sprite width 50
    // Total width = 100 + 200 (buffer) = 300
    // numTiles = ceil(300/50) + 1 = 7
    const instances = createLayerInstances(layers, registry, 100);

    expect(instances).toHaveLength(1);
    expect(instances[0]?.entities.length).toBeGreaterThan(1);

    // Entities should be spaced by sprite width
    const entities = instances[0]?.entities;
    if (entities !== undefined && entities.length >= 2) {
      const first = entities[0];
      const second = entities[1];
      if (first !== undefined && second !== undefined) {
        const spacing = second.x - first.x;
        expect(spacing).toBe(50); // sprite width
      }
    }
  });

  it("uses default width when sizes array is empty", () => {
    const layers: ValidatedLayer[] = [
      {
        name: "empty-sizes",
        type: "sprites",
        parallax: 1.0,
        spriteNames: ["empty"],
        zIndex: 0,
        tile: true,
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
        parallax: 1.0,
        spriteNames: ["multi"],
        zIndex: 0,
        tile: true,
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
        const spacing = second.x - first.x;
        expect(spacing).toBe(60);
      }
    }
  });
});
