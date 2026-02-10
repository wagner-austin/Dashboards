/**
 * Tests for layer-based width generation.
 */

import { describe, it, expect } from "vitest";
import { _test_hooks } from "./widths.js";
import type { LayerSpriteConfig } from "../types.js";

const {
  generateLayerWidths,
  layerToSizeIndex,
  isLayerVisible,
  getVisibleLayerRange,
  layerToWorldZ,
  worldZToLayer,
  WIDTH_CURVE_POWER,
  DEFAULT_SIZE_OFFSET,
} = _test_hooks;

describe("generateLayerWidths", () => {
  it("generates correct number of widths from layerDepth", () => {
    const config: LayerSpriteConfig = {
      minWidth: 15,
      maxWidth: 350,
      defaultLayer: 7,
      layerDepth: 14,
    };

    const widths = generateLayerWidths(config);

    expect(widths).toHaveLength(14);
  });

  it("first width equals minWidth", () => {
    const config: LayerSpriteConfig = {
      minWidth: 20,
      maxWidth: 200,
      defaultLayer: 5,
      layerDepth: 10,
    };

    const widths = generateLayerWidths(config);

    expect(widths[0]).toBe(20);
  });

  it("last width equals maxWidth", () => {
    const config: LayerSpriteConfig = {
      minWidth: 20,
      maxWidth: 200,
      defaultLayer: 5,
      layerDepth: 10,
    };

    const widths = generateLayerWidths(config);

    expect(widths[widths.length - 1]).toBe(200);
  });

  it("widths are monotonically increasing", () => {
    const config: LayerSpriteConfig = {
      minWidth: 15,
      maxWidth: 350,
      defaultLayer: 7,
      layerDepth: 14,
    };

    const widths = generateLayerWidths(config);

    for (let i = 1; i < widths.length; i++) {
      const prev = widths[i - 1];
      const curr = widths[i];
      expect(curr).toBeGreaterThanOrEqual(prev ?? 0);
    }
  });

  it("produces smaller gaps for small widths (power curve)", () => {
    const config: LayerSpriteConfig = {
      minWidth: 15,
      maxWidth: 350,
      defaultLayer: 7,
      layerDepth: 14,
    };

    const widths = generateLayerWidths(config);

    // Gap between first two widths
    const smallGap = (widths[1] ?? 0) - (widths[0] ?? 0);
    // Gap between last two widths
    const largeGap = (widths[widths.length - 1] ?? 0) - (widths[widths.length - 2] ?? 0);

    // Large gap should be bigger than small gap
    expect(largeGap).toBeGreaterThan(smallGap);
  });

  it("handles layerDepth of 1", () => {
    const config: LayerSpriteConfig = {
      minWidth: 50,
      maxWidth: 100,
      defaultLayer: 5,
      layerDepth: 1,
    };

    const widths = generateLayerWidths(config);

    expect(widths).toHaveLength(1);
    expect(widths[0]).toBe(50);
  });

  it("handles layerDepth of 2", () => {
    const config: LayerSpriteConfig = {
      minWidth: 50,
      maxWidth: 100,
      defaultLayer: 5,
      layerDepth: 2,
    };

    const widths = generateLayerWidths(config);

    expect(widths).toHaveLength(2);
    expect(widths[0]).toBe(50);
    expect(widths[1]).toBe(100);
  });

  it("rounds widths to integers", () => {
    const config: LayerSpriteConfig = {
      minWidth: 17,
      maxWidth: 333,
      defaultLayer: 8,
      layerDepth: 15,
    };

    const widths = generateLayerWidths(config);

    for (const width of widths) {
      expect(Number.isInteger(width)).toBe(true);
    }
  });

  it("throws for layerDepth less than 1", () => {
    const config: LayerSpriteConfig = {
      minWidth: 15,
      maxWidth: 350,
      defaultLayer: 7,
      layerDepth: 0,
    };

    expect(() => generateLayerWidths(config)).toThrow("layerDepth must be at least 1");
  });

  it("throws for minWidth >= maxWidth", () => {
    const config: LayerSpriteConfig = {
      minWidth: 100,
      maxWidth: 50,
      defaultLayer: 7,
      layerDepth: 10,
    };

    expect(() => generateLayerWidths(config)).toThrow("minWidth must be less than maxWidth");
  });

  it("throws for minWidth equal to maxWidth", () => {
    const config: LayerSpriteConfig = {
      minWidth: 100,
      maxWidth: 100,
      defaultLayer: 7,
      layerDepth: 10,
    };

    expect(() => generateLayerWidths(config)).toThrow("minWidth must be less than maxWidth");
  });
});

describe("layerToSizeIndex", () => {
  it("returns third largest size at default layer", () => {
    const numSizes = 14;
    const defaultLayer = 7;

    const sizeIdx = layerToSizeIndex(7, defaultLayer, numSizes);

    // Third largest = numSizes - 1 - 2 = 11
    expect(sizeIdx).toBe(11);
  });

  it("returns largest size two layers below default", () => {
    const numSizes = 14;
    const defaultLayer = 7;

    const sizeIdx = layerToSizeIndex(5, defaultLayer, numSizes);

    // Two layers closer = sizeIdx + 2 = 13 (largest)
    expect(sizeIdx).toBe(13);
  });

  it("returns smaller sizes for higher layers", () => {
    const numSizes = 14;
    const defaultLayer = 7;

    const sizeAtDefault = layerToSizeIndex(7, defaultLayer, numSizes);
    const sizeAtHigher = layerToSizeIndex(10, defaultLayer, numSizes);

    expect(sizeAtHigher).toBeLessThan(sizeAtDefault ?? 0);
  });

  it("returns null when layer too close (beyond largest)", () => {
    const numSizes = 14;
    const defaultLayer = 7;

    // Layer 4 would need sizeIdx 14, which is out of bounds
    const sizeIdx = layerToSizeIndex(4, defaultLayer, numSizes);

    expect(sizeIdx).toBeNull();
  });

  it("returns null when layer too far (beyond smallest)", () => {
    const numSizes = 14;
    const defaultLayer = 7;

    // Layer 19 would need sizeIdx -1, which is out of bounds
    const sizeIdx = layerToSizeIndex(19, defaultLayer, numSizes);

    expect(sizeIdx).toBeNull();
  });

  it("returns 0 for smallest visible layer", () => {
    const numSizes = 14;
    const defaultLayer = 7;
    const defaultSizeIdx = numSizes - 1 - DEFAULT_SIZE_OFFSET; // 11

    // Max layer where sizeIdx = 0
    const maxLayer = defaultLayer + defaultSizeIdx; // 18

    const sizeIdx = layerToSizeIndex(maxLayer, defaultLayer, numSizes);

    expect(sizeIdx).toBe(0);
  });

  it("returns numSizes-1 for closest visible layer", () => {
    const numSizes = 14;
    const defaultLayer = 7;
    const defaultSizeIdx = numSizes - 1 - DEFAULT_SIZE_OFFSET; // 11

    // Min layer where sizeIdx = numSizes - 1
    const minLayer = defaultLayer - (numSizes - 1 - defaultSizeIdx); // 5

    const sizeIdx = layerToSizeIndex(minLayer, defaultLayer, numSizes);

    expect(sizeIdx).toBe(13);
  });

  it("returns null for numSizes of 0", () => {
    const sizeIdx = layerToSizeIndex(7, 7, 0);
    expect(sizeIdx).toBeNull();
  });

  it("handles numSizes of 1", () => {
    // With 1 size, defaultSizeIdx = max(0, 0 - 2) = 0
    const sizeIdx = layerToSizeIndex(7, 7, 1);
    expect(sizeIdx).toBe(0);
  });

  it("handles numSizes of 2", () => {
    // With 2 sizes, defaultSizeIdx = max(0, 1 - 2) = 0
    const sizeIdx = layerToSizeIndex(7, 7, 2);
    expect(sizeIdx).toBe(0);
  });

  it("handles numSizes of 3", () => {
    // With 3 sizes, defaultSizeIdx = max(0, 2 - 2) = 0
    // Third largest is index 0 when there are only 3 sizes
    const sizeIdx = layerToSizeIndex(7, 7, 3);
    expect(sizeIdx).toBe(0);
  });

  it("handles numSizes of 4", () => {
    // With 4 sizes, defaultSizeIdx = max(0, 3 - 2) = 1
    const sizeIdx = layerToSizeIndex(7, 7, 4);
    expect(sizeIdx).toBe(1);
  });
});

describe("isLayerVisible", () => {
  it("returns true for layer at default", () => {
    expect(isLayerVisible(7, 7, 14)).toBe(true);
  });

  it("returns true for layers in range", () => {
    expect(isLayerVisible(5, 7, 14)).toBe(true);
    expect(isLayerVisible(10, 7, 14)).toBe(true);
  });

  it("returns false for layer too close", () => {
    expect(isLayerVisible(4, 7, 14)).toBe(false);
  });

  it("returns false for layer too far", () => {
    expect(isLayerVisible(19, 7, 14)).toBe(false);
  });

  it("returns false for zero sizes", () => {
    expect(isLayerVisible(7, 7, 0)).toBe(false);
  });
});

describe("getVisibleLayerRange", () => {
  it("returns correct range for 14 sizes at default 7", () => {
    const range = getVisibleLayerRange(7, 14);

    // defaultSizeIdx = 14 - 1 - 2 = 11
    // minLayer = 7 - (13 - 11) = 5
    // maxLayer = 7 + 11 = 18
    expect(range.minLayer).toBe(5);
    expect(range.maxLayer).toBe(18);
  });

  it("returns span equal to numSizes", () => {
    const range = getVisibleLayerRange(10, 20);

    const span = range.maxLayer - range.minLayer + 1;
    expect(span).toBe(20);
  });

  it("handles small numSizes", () => {
    const range = getVisibleLayerRange(5, 3);

    // defaultSizeIdx = max(0, 2 - 2) = 0
    // minLayer = 5 - (2 - 0) = 3
    // maxLayer = 5 + 0 = 5
    expect(range.minLayer).toBe(3);
    expect(range.maxLayer).toBe(5);
  });
});

describe("layerToWorldZ", () => {
  it("converts layer 0 to Z 50", () => {
    expect(layerToWorldZ(0)).toBe(50);
  });

  it("converts layer 10 to Z 100", () => {
    expect(layerToWorldZ(10)).toBe(100);
  });

  it("converts layer 20 to Z 150", () => {
    expect(layerToWorldZ(20)).toBe(150);
  });

  it("handles negative layers", () => {
    expect(layerToWorldZ(-2)).toBe(40);
  });
});

describe("worldZToLayer", () => {
  it("converts Z 50 to layer 0", () => {
    expect(worldZToLayer(50)).toBe(0);
  });

  it("converts Z 100 to layer 10", () => {
    expect(worldZToLayer(100)).toBe(10);
  });

  it("converts Z 150 to layer 20", () => {
    expect(worldZToLayer(150)).toBe(20);
  });

  it("is inverse of layerToWorldZ", () => {
    for (let layer = -5; layer <= 30; layer++) {
      const z = layerToWorldZ(layer);
      const backToLayer = worldZToLayer(z);
      expect(backToLayer).toBe(layer);
    }
  });
});

describe("constants", () => {
  it("WIDTH_CURVE_POWER is greater than 1", () => {
    expect(WIDTH_CURVE_POWER).toBeGreaterThan(1);
  });

  it("DEFAULT_SIZE_OFFSET is 2", () => {
    expect(DEFAULT_SIZE_OFFSET).toBe(2);
  });
});
