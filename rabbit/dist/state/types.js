/**
 * Game state types for the ASCII animation engine.
 * Immutable TypedDicts with full type safety.
 */
/** Create initial game state */
export function createInitialState(viewport, sprites) {
    return {
        viewport,
        facingRight: false,
        currentAnimation: "idle",
        bunnyFrameIdx: 0,
        isJumping: false,
        jumpFrameIdx: 0,
        isWalking: false,
        groundScrollX: 0,
        treeFrameIdx: 0,
        treeDirection: 1,
        treeSizeIdx: 1,
        treeTargetSizeIdx: 1,
        treeSizeTransitionProgress: 0,
        treeCenterX: viewport.width + 60,
        currentSpeedMultiplier: 1.0,
        ...sprites,
    };
}
/** Speed multiplier calculation for a given tree size index */
export function getSpeedMultiplier(treeSizeIdx) {
    return 0.5 + treeSizeIdx * 0.5;
}
/** Ease-in-out S-curve for smooth transitions */
export function easeInOut(progress) {
    return progress < 0.5
        ? 2 * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 2) / 2;
}
/** Lerp between two values with optional easing */
export function lerp(start, end, progress, eased = true) {
    const t = eased ? easeInOut(progress) : progress;
    return start + (end - start) * t;
}
//# sourceMappingURL=types.js.map