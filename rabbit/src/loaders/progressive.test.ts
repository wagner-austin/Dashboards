/**
 * Tests for progressive sprite loading module.
 */

import { describe, it, expect } from "vitest";
import type { Config, FrameSet } from "../types.js";
import { _test_hooks } from "./progressive.js";

const {
  createMutableSpriteRegistry,
  getOrCreateSpriteArray,
  insertSortedByWidth,
  collectTreeWidths,
  getGrassSpriteNames,
  getTreeSpriteNames,
  getSpriteWidthsFromConfig,
} = _test_hooks;

function createTestConfig(): Config {
  return {
    sprites: {
      tree1: {
        widths: [15, 30, 100, 200],
      },
      tree2: {
        widths: [20, 50, 150],
      },
      grass: {
        widths: [160],
      },
    },
    layers: [
      { name: "sky", type: "static" },
      { name: "grass-front", sprites: ["grass"], tile: true },
    ],
    settings: {
      fps: 60,
      jumpSpeed: 58,
      scrollSpeed: 36,
    },
    autoLayers: {
      sprites: ["tree1", "tree2"],
      minLayer: 8,
      maxLayer: 30,
    },
  };
}

describe("createMutableSpriteRegistry", () => {
  it("creates empty arrays for each sprite name", () => {
    const registry = createMutableSpriteRegistry(["tree1", "tree2", "grass"]);

    expect(registry.sprites.size).toBe(3);
    expect(registry.sprites.get("tree1")).toEqual([]);
    expect(registry.sprites.get("tree2")).toEqual([]);
    expect(registry.sprites.get("grass")).toEqual([]);
  });

  it("handles empty sprite names array", () => {
    const registry = createMutableSpriteRegistry([]);

    expect(registry.sprites.size).toBe(0);
  });

  it("creates independent arrays for each sprite", () => {
    const registry = createMutableSpriteRegistry(["a", "b"]);

    const arrayA = registry.sprites.get("a");
    const arrayB = registry.sprites.get("b");

    expect(arrayA).not.toBe(arrayB);
  });
});

describe("getOrCreateSpriteArray", () => {
  it("returns existing array for known sprite", () => {
    const registry = createMutableSpriteRegistry(["tree1"]);
    const existingArray = registry.sprites.get("tree1");

    const result = getOrCreateSpriteArray(registry, "tree1");

    expect(result).toBe(existingArray);
  });

  it("creates new array for unknown sprite", () => {
    const registry = createMutableSpriteRegistry(["tree1"]);

    const result = getOrCreateSpriteArray(registry, "newSprite");

    expect(result).toEqual([]);
    expect(registry.sprites.get("newSprite")).toBe(result);
  });

  it("returns same array on subsequent calls", () => {
    const registry = createMutableSpriteRegistry([]);

    const first = getOrCreateSpriteArray(registry, "sprite");
    const second = getOrCreateSpriteArray(registry, "sprite");

    expect(first).toBe(second);
  });
});

describe("insertSortedByWidth", () => {
  it("inserts into empty array", () => {
    const sizes: FrameSet[] = [];
    const frameSet: FrameSet = { width: 100, frames: ["frame1"] };

    insertSortedByWidth(sizes, frameSet);

    expect(sizes).toEqual([{ width: 100, frames: ["frame1"] }]);
  });

  it("inserts at beginning when smaller than all", () => {
    const sizes: FrameSet[] = [
      { width: 50, frames: ["a"] },
      { width: 100, frames: ["b"] },
    ];

    insertSortedByWidth(sizes, { width: 25, frames: ["new"] });

    expect(sizes.map((s) => s.width)).toEqual([25, 50, 100]);
  });

  it("inserts at end when larger than all", () => {
    const sizes: FrameSet[] = [
      { width: 50, frames: ["a"] },
      { width: 100, frames: ["b"] },
    ];

    insertSortedByWidth(sizes, { width: 200, frames: ["new"] });

    expect(sizes.map((s) => s.width)).toEqual([50, 100, 200]);
  });

  it("inserts in middle at correct position", () => {
    const sizes: FrameSet[] = [
      { width: 25, frames: ["a"] },
      { width: 100, frames: ["b"] },
      { width: 200, frames: ["c"] },
    ];

    insertSortedByWidth(sizes, { width: 75, frames: ["new"] });

    expect(sizes.map((s) => s.width)).toEqual([25, 75, 100, 200]);
  });

  it("handles duplicate widths by inserting at correct position", () => {
    const sizes: FrameSet[] = [
      { width: 50, frames: ["a"] },
      { width: 100, frames: ["b"] },
    ];

    insertSortedByWidth(sizes, { width: 50, frames: ["dup"] });

    // Widths should remain sorted (equal values are adjacent)
    expect(sizes.map((s) => s.width)).toEqual([50, 50, 100]);
    // Duplicate inserted before existing (stable sort not required)
    expect(sizes[0]?.frames).toEqual(["dup"]);
    expect(sizes[1]?.frames).toEqual(["a"]);
  });
});

describe("collectTreeWidths", () => {
  it("collects widths from multiple tree sprites", () => {
    const config = createTestConfig();

    const entries = collectTreeWidths(config, ["tree1", "tree2"]);

    expect(entries.length).toBe(7); // 4 from tree1 + 3 from tree2
  });

  it("sorts entries by width descending (largest first)", () => {
    const config = createTestConfig();

    const entries = collectTreeWidths(config, ["tree1", "tree2"]);

    const widths = entries.map((e) => e.width);
    expect(widths).toEqual([200, 150, 100, 50, 30, 20, 15]);
  });

  it("preserves sprite names for each entry", () => {
    const config = createTestConfig();

    const entries = collectTreeWidths(config, ["tree1", "tree2"]);

    const first = entries[0];
    expect(first?.spriteName).toBe("tree1");
    expect(first?.width).toBe(200);

    const second = entries[1];
    expect(second?.spriteName).toBe("tree2");
    expect(second?.width).toBe(150);
  });

  it("handles empty tree names array", () => {
    const config = createTestConfig();

    const entries = collectTreeWidths(config, []);

    expect(entries).toEqual([]);
  });

  it("skips sprites without widths", () => {
    const config: Config = {
      sprites: {
        tree1: { source: "test.gif" }, // No widths
      },
      layers: [],
      settings: { fps: 60, jumpSpeed: 58, scrollSpeed: 36 },
    };

    const entries = collectTreeWidths(config, ["tree1"]);

    expect(entries).toEqual([]);
  });

  it("skips unknown sprites", () => {
    const config = createTestConfig();

    const entries = collectTreeWidths(config, ["unknown"]);

    expect(entries).toEqual([]);
  });
});

describe("getGrassSpriteNames", () => {
  it("finds grass sprites in layers", () => {
    const config = createTestConfig();

    const names = getGrassSpriteNames(config);

    expect(names).toEqual(["grass"]);
  });

  it("returns empty for layers without sprites", () => {
    const config: Config = {
      sprites: {},
      layers: [{ name: "sky", type: "static" }],
      settings: { fps: 60, jumpSpeed: 58, scrollSpeed: 36 },
    };

    const names = getGrassSpriteNames(config);

    expect(names).toEqual([]);
  });

  it("finds multiple grass sprites", () => {
    const config: Config = {
      sprites: {},
      layers: [
        { name: "grass-front", sprites: ["grass1", "grass2"] },
        { name: "grass-back", sprites: ["grassBack"] },
      ],
      settings: { fps: 60, jumpSpeed: 58, scrollSpeed: 36 },
    };

    const names = getGrassSpriteNames(config);

    expect(names).toEqual(["grass1", "grass2", "grassBack"]);
  });

  it("ignores non-grass sprites", () => {
    const config: Config = {
      sprites: {},
      layers: [{ name: "other", sprites: ["tree1", "rock"] }],
      settings: { fps: 60, jumpSpeed: 58, scrollSpeed: 36 },
    };

    const names = getGrassSpriteNames(config);

    expect(names).toEqual([]);
  });
});

describe("getTreeSpriteNames", () => {
  it("returns sprites from autoLayers config", () => {
    const config = createTestConfig();

    const names = getTreeSpriteNames(config);

    expect(names).toEqual(["tree1", "tree2"]);
  });

  it("returns empty array when no autoLayers", () => {
    const config: Config = {
      sprites: {},
      layers: [],
      settings: { fps: 60, jumpSpeed: 58, scrollSpeed: 36 },
    };

    const names = getTreeSpriteNames(config);

    expect(names).toEqual([]);
  });
});

describe("getSpriteWidthsFromConfig", () => {
  it("returns widths for known sprite", () => {
    const config = createTestConfig();

    const widths = getSpriteWidthsFromConfig(config, "tree1");

    expect(widths).toEqual([15, 30, 100, 200]);
  });

  it("returns empty for unknown sprite", () => {
    const config = createTestConfig();

    const widths = getSpriteWidthsFromConfig(config, "unknown");

    expect(widths).toEqual([]);
  });

  it("returns empty for sprite without widths", () => {
    const config: Config = {
      sprites: {
        noWidths: { source: "test.gif" },
      },
      layers: [],
      settings: { fps: 60, jumpSpeed: 58, scrollSpeed: 36 },
    };

    const widths = getSpriteWidthsFromConfig(config, "noWidths");

    expect(widths).toEqual([]);
  });
});
