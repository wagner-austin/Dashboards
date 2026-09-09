/**
 * Tests for occlusion between the stacked render layers.
 */

import { describe, it, expect } from "vitest";
import { occludeStackedBuffers, _test_hooks, type LayerBuffers } from "./occlusion.js";

const { blankCoveredCells } = _test_hooks;

/** Build a mutable buffer from one string per row. */
function bufferFrom(rows: readonly string[]): string[][] {
  return rows.map((row) => Array.from(row));
}

/** Whether a buffer holds a visible character at this cell. */
function paintedAt(rows: readonly string[], row: number, col: number): boolean {
  const line = rows[row];
  if (line === undefined) {
    return false;
  }
  const cell = line[col];
  return cell !== undefined && cell !== " ";
}

/** Read a buffer back as one string per row. */
function rowsOf(buffer: readonly (readonly string[])[]): string[] {
  return buffer.map((row) => row.join(""));
}

/** Build the three buffers from one string per row each. */
function stackFrom(
  world: readonly string[],
  actor: readonly string[],
  foreground: readonly string[]
): LayerBuffers {
  return {
    world: bufferFrom(world),
    actor: bufferFrom(actor),
    foreground: bufferFrom(foreground),
  };
}

describe("blankCoveredCells", () => {
  it("blanks a lower cell that the upper layer paints", () => {
    const lower = bufferFrom(["###"]);

    blankCoveredCells(lower, bufferFrom(["#  "]));

    expect(rowsOf(lower)).toEqual([" ##"]);
  });

  it("leaves a lower cell that the upper layer leaves as a space", () => {
    // Spaces stay transparent - that half of the split was always right, and
    // blanking must not tighten it into an opaque box around the sprite.
    const lower = bufferFrom(["ABC"]);

    blankCoveredCells(lower, bufferFrom(["   "]));

    expect(rowsOf(lower)).toEqual(["ABC"]);
  });

  it("leaves lower cells past the end of a shorter upper row", () => {
    const lower = bufferFrom(["ABCDE"]);

    blankCoveredCells(lower, bufferFrom(["##"]));

    expect(rowsOf(lower)).toEqual(["  CDE"]);
  });

  it("skips rows the lower buffer does not hold", () => {
    const lower: string[][] = [];
    lower.length = 2;
    lower[1] = Array.from("AB");

    blankCoveredCells(lower, bufferFrom(["##", "##"]));

    expect(lower[0]).toBeUndefined();
    expect(lower[1]).toEqual([" ", " "]);
  });

  it("skips rows the upper buffer does not hold", () => {
    const lower = bufferFrom(["AB", "CD"]);

    blankCoveredCells(lower, bufferFrom(["##"]));

    expect(rowsOf(lower)).toEqual(["  ", "CD"]);
  });
});

describe("occludeStackedBuffers", () => {
  it("keeps the frontmost glyph and blanks the ones behind it", () => {
    // The bug this exists for: three transparent elements painted all three
    // of these characters into one cell, on top of each other.
    const buffers = stackFrom(["T"], ["R"], ["G"]);

    occludeStackedBuffers(buffers);

    expect(rowsOf(buffers.world)).toEqual([" "]);
    expect(rowsOf(buffers.actor)).toEqual([" "]);
    expect(rowsOf(buffers.foreground)).toEqual(["G"]);
  });

  it("clears the world where the foreground paints and the actor does not", () => {
    // The trap in doing this pairwise between adjacent layers: masking the
    // actor by the foreground first, then the world by the actor, leaves the
    // world visible under foreground grass wherever the actor was blank.
    const buffers = stackFrom(["T"], [" "], ["G"]);

    occludeStackedBuffers(buffers);

    expect(rowsOf(buffers.world)).toEqual([" "]);
    expect(rowsOf(buffers.foreground)).toEqual(["G"]);
  });

  it("clears the world where the actor paints", () => {
    const buffers = stackFrom(["T"], ["R"], [" "]);

    occludeStackedBuffers(buffers);

    expect(rowsOf(buffers.world)).toEqual([" "]);
    expect(rowsOf(buffers.actor)).toEqual(["R"]);
  });

  it("clears the actor where the foreground paints", () => {
    const buffers = stackFrom([" "], ["R"], ["G"]);

    occludeStackedBuffers(buffers);

    expect(rowsOf(buffers.actor)).toEqual([" "]);
    expect(rowsOf(buffers.foreground)).toEqual(["G"]);
  });

  it("leaves a layer alone where nothing nearer paints", () => {
    const buffers = stackFrom(["TT."], ["   "], ["   "]);

    occludeStackedBuffers(buffers);

    expect(rowsOf(buffers.world)).toEqual(["TT."]);
  });

  it("reproduces the single-buffer result cell for cell", () => {
    // What one shared buffer produced: the last non-space write to each cell,
    // in draw order world -> actor -> foreground. Built here by hand so the
    // expectation does not borrow the implementation being tested.
    const buffers = stackFrom(
      ["TT.T", "T..T"],
      [" RR ", " R  "],
      ["  G ", "GG  "]
    );

    occludeStackedBuffers(buffers);

    expect(rowsOf(buffers.world)).toEqual(["T  T", "  .T"]);
    expect(rowsOf(buffers.actor)).toEqual([" R  ", "    "]);
    expect(rowsOf(buffers.foreground)).toEqual(["  G ", "GG  "]);
  });

  it("never leaves a glyph in the same cell of two layers", () => {
    const buffers = stackFrom(
      ["####", "####"],
      ["##  ", "  ##"],
      ["#  #", " ## "]
    );

    occludeStackedBuffers(buffers);

    const painted = [buffers.world, buffers.actor, buffers.foreground].map(rowsOf);
    for (let row = 0; row < 2; row++) {
      for (let col = 0; col < 4; col++) {
        const drawn = painted.filter((layer) => paintedAt(layer, row, col));
        expect(drawn.length).toBeLessThanOrEqual(1);
      }
    }
  });
});
