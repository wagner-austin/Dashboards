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
  // Viewport
  readonly viewport: ViewportState;

  // Bunny direction and animation
  readonly facingRight: boolean;
  readonly currentAnimation: BunnyAnimation;
  readonly bunnyFrameIdx: number;
  readonly isJumping: boolean;
  readonly jumpFrameIdx: number;

  // Walk controls
  readonly isWalking: boolean;

  // Ground scroll position
  readonly groundScrollX: number;

  // Tree animation state
  readonly treeFrameIdx: number;
  readonly treeDirection: number;
  readonly treeSizeIdx: number;
  readonly treeTargetSizeIdx: number;
  readonly treeSizeTransitionProgress: number;
  readonly treeCenterX: number;
  readonly currentSpeedMultiplier: number;

  // Sprite data
  readonly bunnyWalkFramesLeft: readonly string[];
  readonly bunnyWalkFramesRight: readonly string[];
  readonly bunnyJumpFramesLeft: readonly string[];
  readonly bunnyJumpFramesRight: readonly string[];
  readonly bunnyIdleFramesLeft: readonly string[];
  readonly bunnyIdleFramesRight: readonly string[];
  readonly treeSizes: readonly TreeSizeConfig[];
}

/** Create initial game state */
export function createInitialState(
  viewport: ViewportState,
  sprites: {
    bunnyWalkFramesLeft: readonly string[];
    bunnyWalkFramesRight: readonly string[];
    bunnyJumpFramesLeft: readonly string[];
    bunnyJumpFramesRight: readonly string[];
    bunnyIdleFramesLeft: readonly string[];
    bunnyIdleFramesRight: readonly string[];
    treeSizes: readonly TreeSizeConfig[];
  }
): GameState {
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
export function getSpeedMultiplier(treeSizeIdx: number): number {
  return 0.5 + treeSizeIdx * 0.5;
}

/** Ease-in-out S-curve for smooth transitions */
export function easeInOut(progress: number): number {
  return progress < 0.5
    ? 2 * progress * progress
    : 1 - Math.pow(-2 * progress + 2, 2) / 2;
}

/** Lerp between two values with optional easing */
export function lerp(start: number, end: number, progress: number, eased = true): number {
  const t = eased ? easeInOut(progress) : progress;
  return start + (end - start) * t;
}
