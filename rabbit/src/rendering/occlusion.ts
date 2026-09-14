/**
 * Occlusion between the three stacked render layers.
 *
 * The scene draws into three stacked <pre> elements so the actor can carry its
 * own colour without the buffer holding a colour per cell. That split
 * preserved draw ORDER - DOM stacking puts the actor over the world and the
 * foreground over both - but it did not preserve OVERWRITE, and the overwrite
 * is what "covers" meant.
 *
 * A <pre> has no background, so it is transparent everywhere its glyphs' ink
 * is not, and not only where it holds spaces. Two layers holding a non-space
 * character in the same cell are therefore BOTH painted, superimposed: the
 * rabbit standing in front of a tree drew the rabbit's glyph and the tree's
 * glyph into one character cell. The single-buffer engine wrote
 * `bufferRow[col] = ch` - a replacement - so the last writer was the only
 * writer, and that is the property the split silently dropped.
 *
 * This module restores it. Every cell keeps only its frontmost non-space
 * character and the layers behind it are blanked back to spaces, which are
 * transparent and are the one thing the split did get right. What the three
 * elements emit afterwards is cell-for-cell what one shared buffer emitted.
 */

/**
 * The three render buffers, one per stacked layer.
 *
 * Named rather than indexed, mirroring ScreenLayers and LayerColors: the layer
 * set is fixed by the markup the engine draws into, not a list that grows.
 *
 * world: Background layers, trees, and the ground.
 * actor: The character, and nothing else.
 * foreground: Layers drawn in front of the actor.
 */
export interface LayerBuffers {
  readonly world: string[][];
  readonly actor: string[][];
  readonly foreground: string[][];
}

/**
 * Blank every cell of `lower` that `upper` paints.
 *
 * Mutates `lower` in place, like the drawing functions that filled it. Cells
 * `upper` leaves as spaces are untouched, so the lower layer still shows
 * through everywhere the nearer one draws nothing.
 *
 * Args:
 *     lower: Buffer of the layer further from the camera. Mutated.
 *     upper: Buffer of the layer nearer the camera. Read only.
 */
function blankCoveredCells(
  lower: string[][],
  upper: readonly (readonly string[])[]
): void {
  for (let row = 0; row < lower.length; row++) {
    const lowerCells = lower[row];
    if (lowerCells === undefined) {
      continue;
    }
    const upperCells = upper[row];
    if (upperCells === undefined) {
      continue;
    }
    for (let col = 0; col < lowerCells.length; col++) {
      const upperCell = upperCells[col];
      if (upperCell !== undefined && upperCell !== " ") {
        lowerCells[col] = " ";
      }
    }
  }
}

/**
 * Resolve the overlap between the stacked buffers, front to back.
 *
 * After this returns, no cell holds a non-space character in more than one
 * buffer: the frontmost writer of each cell keeps it and the rest hold a
 * space. Occlusion then survives being painted into three transparent
 * elements instead of one opaque buffer.
 *
 * The passes run front to back so the actor's own coverage is already reduced
 * by the foreground before the world is measured against it. Blanking the
 * world against the foreground first is what makes that safe: the world ends
 * up cleared wherever EITHER nearer layer draws, never only where the actor
 * survived.
 *
 * Args:
 *     buffers: The three render buffers. All three are mutated.
 */
export function occludeStackedBuffers(buffers: LayerBuffers): void {
  blankCoveredCells(buffers.actor, buffers.foreground);
  blankCoveredCells(buffers.world, buffers.foreground);
  blankCoveredCells(buffers.world, buffers.actor);
}

/** Test hooks for internal functions */
export const _test_hooks = {
  blankCoveredCells,
  occludeStackedBuffers,
};
