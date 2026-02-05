/**
 * Tree entity - state, zoom, and frame selection.
 */
import { createAnimationTimer } from "../loaders/sprites.js";
import { GROUND_TILE } from "../rendering/Ground.js";
export function createInitialTreeState(viewportWidth) {
    return {
        frameIdx: 0,
        direction: 1,
        sizeIdx: 2, // Start at largest size (most zoomed in)
        targetSizeIdx: 2,
        sizeTransitionProgress: 0,
        centerX: Math.floor(viewportWidth / 3),
    };
}
export function createTreeTimer(state, sizes, intervalMs) {
    return createAnimationTimer(intervalMs, () => {
        const currentSize = sizes[state.sizeIdx];
        if (currentSize === undefined)
            return;
        const frameCount = currentSize.frames.length;
        state.frameIdx += state.direction;
        if (state.frameIdx >= frameCount) {
            state.frameIdx = frameCount - 2;
            state.direction = -1;
        }
        else if (state.frameIdx < 0) {
            state.frameIdx = 1;
            state.direction = 1;
        }
    });
}
// Ground rows in tree ASCII: w60=3, w120=6, w180=9
const TREE_GROUND_ROWS = [3, 6, 9];
export function calcTreeY(treeHeight, sizeIdx, viewportHeight) {
    const groundRows = TREE_GROUND_ROWS[sizeIdx] ?? 6;
    const sceneGroundHeight = GROUND_TILE.length;
    return viewportHeight - sceneGroundHeight - treeHeight + groundRows;
}
export function getTreeFrame(state, sizes) {
    const currentSize = sizes[state.sizeIdx];
    if (currentSize === undefined)
        return null;
    const frame = currentSize.frames[state.frameIdx];
    if (frame === undefined)
        return null;
    return {
        lines: frame.split("\n"),
        width: currentSize.width,
    };
}
export function getTreeTransitionFrames(state, sizes) {
    const currentSize = sizes[state.sizeIdx];
    if (currentSize === undefined)
        return null;
    const targetIdx = state.sizeIdx < state.targetSizeIdx
        ? state.sizeIdx + 1
        : state.sizeIdx - 1;
    const targetSize = sizes[targetIdx];
    if (targetSize === undefined)
        return null;
    const currentFrame = currentSize.frames[state.frameIdx];
    const targetFrame = targetSize.frames[state.frameIdx % targetSize.frames.length];
    if (currentFrame === undefined || targetFrame === undefined)
        return null;
    return {
        current: { lines: currentFrame.split("\n"), width: currentSize.width },
        target: { lines: targetFrame.split("\n"), width: targetSize.width },
        targetIdx,
    };
}
//# sourceMappingURL=Tree.js.map