/**
 * Tests for Ground rendering.
 */

import { describe, it, expect } from "vitest";
import { GROUND_TILE, GROUND_TILE_WIDTH, drawGround } from "./Ground.js";

describe("GROUND_TILE", () => {
  it("has 6 rows", () => {
    expect(GROUND_TILE.length).toBe(6);
  });

  it("has consistent width across all rows", () => {
    for (const row of GROUND_TILE) {
      expect(row.length).toBe(GROUND_TILE_WIDTH);
    }
  });
});

describe("GROUND_TILE_WIDTH", () => {
  it("equals the width of the first tile row", () => {
    expect(GROUND_TILE_WIDTH).toBe(60);
  });
});

describe("drawGround", () => {
  function createBuffer(width: number, height: number): string[][] {
    return Array.from({ length: height }, () => Array(width).fill(" ") as string[]);
  }

  it("draws ground at bottom of buffer", () => {
    const buffer = createBuffer(20, 10);
    drawGround(buffer, 0, 20, 10);

    // Ground should be in bottom 6 rows
    const topRows = buffer.slice(0, 4);
    const bottomRows = buffer.slice(4);

    // Top rows should be mostly empty
    for (const row of topRows) {
      expect(row.every((c) => c === " ")).toBe(true);
    }

    // Bottom rows should have some content (dots or plus signs)
    const hasContent = bottomRows.some((row) =>
      row.some((c) => c !== " ")
    );
    expect(hasContent).toBe(true);
  });

  it("scrolls with offset", () => {
    const buffer1 = createBuffer(20, 10);
    const buffer2 = createBuffer(20, 10);

    drawGround(buffer1, 0, 20, 10);
    drawGround(buffer2, 5, 20, 10);

    // Buffers should be different due to offset
    const str1 = buffer1.map((r) => r.join("")).join("\n");
    const str2 = buffer2.map((r) => r.join("")).join("\n");
    expect(str1).not.toBe(str2);
  });

  it("wraps tile pattern", () => {
    const buffer1 = createBuffer(20, 10);
    const buffer2 = createBuffer(20, 10);

    drawGround(buffer1, 0, 20, 10);
    drawGround(buffer2, GROUND_TILE_WIDTH, 20, 10);

    // Should be identical after one full tile width
    const str1 = buffer1.map((r) => r.join("")).join("\n");
    const str2 = buffer2.map((r) => r.join("")).join("\n");
    expect(str1).toBe(str2);
  });

  it("handles negative offset", () => {
    const buffer = createBuffer(20, 10);
    // Should not throw
    expect(() => {
      drawGround(buffer, -10, 20, 10);
    }).not.toThrow();
  });

  it("handles zero dimensions gracefully", () => {
    const buffer = createBuffer(0, 0);
    expect(() => {
      drawGround(buffer, 0, 0, 0);
    }).not.toThrow();
  });

  it("handles sparse buffer array gracefully", () => {
    // Create a sparse array with holes
    const sparseBuffer: string[][] = [];
    sparseBuffer.length = 10;
    // Only set some rows, leaving holes
    sparseBuffer[0] = Array(20).fill(" ") as string[];
    sparseBuffer[9] = Array(20).fill(" ") as string[];
    // Middle rows are undefined (holes)

    // Should not throw - the undefined check handles sparse arrays
    expect(() => {
      drawGround(sparseBuffer, 0, 20, 10);
    }).not.toThrow();
  });
});
