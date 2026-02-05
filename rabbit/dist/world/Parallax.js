/**
 * Parallax scrolling calculations.
 * Pure functions for calculating scroll positions and speed transitions.
 */
import { getSpeedMultiplier, lerp } from "../utils/math.js";
/** Calculate new scroll positions */
export function calculateScrollUpdate(groundScrollX, treeCenterX, scrollAmount, facingRight, viewportWidth, maxTreeWidth) {
    let newGroundX = groundScrollX;
    let newTreeX = treeCenterX;
    if (facingRight) {
        newGroundX -= scrollAmount;
        newTreeX -= scrollAmount;
        if (newTreeX < -maxTreeWidth / 2) {
            newTreeX = viewportWidth + maxTreeWidth / 2;
        }
    }
    else {
        newGroundX += scrollAmount;
        newTreeX += scrollAmount;
        if (newTreeX > viewportWidth + maxTreeWidth / 2) {
            newTreeX = -maxTreeWidth / 2;
        }
    }
    return {
        groundScrollX: newGroundX,
        treeCenterX: newTreeX,
    };
}
/** Update speed transition state */
export function updateSpeedTransition(treeSizeIdx, treeTargetSizeIdx, treeSizeTransitionProgress, deltaTimeMs, transitionDurationMs) {
    const isTransitioning = treeSizeIdx !== treeTargetSizeIdx;
    if (!isTransitioning) {
        return {
            treeSizeIdx,
            treeSizeTransitionProgress: 0,
            currentSpeedMultiplier: getSpeedMultiplier(treeSizeIdx),
        };
    }
    const newProgress = treeSizeTransitionProgress + deltaTimeMs / transitionDurationMs;
    if (newProgress >= 1) {
        // Transition complete, move to next size
        const newSizeIdx = treeSizeIdx < treeTargetSizeIdx
            ? treeSizeIdx + 1
            : treeSizeIdx - 1;
        return {
            treeSizeIdx: newSizeIdx,
            treeSizeTransitionProgress: 0,
            currentSpeedMultiplier: getSpeedMultiplier(newSizeIdx),
        };
    }
    // Still transitioning, lerp the speed
    const currentMultiplier = getSpeedMultiplier(treeSizeIdx);
    const targetIdx = treeSizeIdx < treeTargetSizeIdx
        ? treeSizeIdx + 1
        : treeSizeIdx - 1;
    const targetMultiplier = getSpeedMultiplier(targetIdx);
    return {
        treeSizeIdx,
        treeSizeTransitionProgress: newProgress,
        currentSpeedMultiplier: lerp(currentMultiplier, targetMultiplier, newProgress),
    };
}
//# sourceMappingURL=Parallax.js.map