/**
 * Parallax scrolling calculations.
 * Pure functions for calculating scroll positions and speed transitions.
 */
/** Result of a scroll update */
export interface ScrollUpdate {
    readonly groundScrollX: number;
    readonly treeCenterX: number;
}
/** Result of a speed transition update */
export interface SpeedTransitionUpdate {
    readonly treeSizeIdx: number;
    readonly treeSizeTransitionProgress: number;
    readonly currentSpeedMultiplier: number;
}
/** Calculate new scroll positions */
export declare function calculateScrollUpdate(groundScrollX: number, treeCenterX: number, scrollAmount: number, facingRight: boolean, viewportWidth: number, maxTreeWidth: number): ScrollUpdate;
/** Update speed transition state */
export declare function updateSpeedTransition(treeSizeIdx: number, treeTargetSizeIdx: number, treeSizeTransitionProgress: number, deltaTimeMs: number, transitionDurationMs: number): SpeedTransitionUpdate;
//# sourceMappingURL=Parallax.d.ts.map