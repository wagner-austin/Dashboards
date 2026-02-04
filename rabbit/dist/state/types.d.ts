/**
 * Game state types for the ASCII animation engine.
 * Immutable TypedDicts with full type safety.
 */
/** Viewport dimensions and character measurements */
export interface ViewportState {
    readonly width: number;
    readonly height: number;
    readonly charW: number;
    readonly charH: number;
}
/** Animation type for the bunny */
export type BunnyAnimation = "walk" | "jump" | "idle";
/** Tree size configuration */
export interface TreeSizeConfig {
    readonly width: number;
    readonly frames: readonly string[];
}
/** Immutable game state */
export interface GameState {
    readonly viewport: ViewportState;
    readonly facingRight: boolean;
    readonly currentAnimation: BunnyAnimation;
    readonly bunnyFrameIdx: number;
    readonly isJumping: boolean;
    readonly jumpFrameIdx: number;
    readonly isWalking: boolean;
    readonly groundScrollX: number;
    readonly treeFrameIdx: number;
    readonly treeDirection: number;
    readonly treeSizeIdx: number;
    readonly treeTargetSizeIdx: number;
    readonly treeSizeTransitionProgress: number;
    readonly treeCenterX: number;
    readonly currentSpeedMultiplier: number;
    readonly bunnyWalkFramesLeft: readonly string[];
    readonly bunnyWalkFramesRight: readonly string[];
    readonly bunnyJumpFramesLeft: readonly string[];
    readonly bunnyJumpFramesRight: readonly string[];
    readonly bunnyIdleFramesLeft: readonly string[];
    readonly bunnyIdleFramesRight: readonly string[];
    readonly treeSizes: readonly TreeSizeConfig[];
}
/** Create initial game state */
export declare function createInitialState(viewport: ViewportState, sprites: {
    bunnyWalkFramesLeft: readonly string[];
    bunnyWalkFramesRight: readonly string[];
    bunnyJumpFramesLeft: readonly string[];
    bunnyJumpFramesRight: readonly string[];
    bunnyIdleFramesLeft: readonly string[];
    bunnyIdleFramesRight: readonly string[];
    treeSizes: readonly TreeSizeConfig[];
}): GameState;
/** Speed multiplier calculation for a given tree size index */
export declare function getSpeedMultiplier(treeSizeIdx: number): number;
/** Ease-in-out S-curve for smooth transitions */
export declare function easeInOut(progress: number): number;
/** Lerp between two values with optional easing */
export declare function lerp(start: number, end: number, progress: number, eased?: boolean): number;
//# sourceMappingURL=types.d.ts.map