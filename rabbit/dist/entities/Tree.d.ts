/**
 * Tree entity - state, zoom, and frame selection.
 */
import { type AnimationTimer } from "../loaders/sprites.js";
import { type EntityTransitionState } from "./EntityTransition.js";
/** Tree X position as fraction of viewport width (negative = left of center). */
export declare const TREE_X_RATIO: number;
/**
 * Tree size variant with frames.
 *
 * width: Sprite width in characters.
 * frames: Animation frames for this size.
 */
export interface TreeSize {
    readonly width: number;
    readonly frames: readonly string[];
}
/**
 * Tree entity state.
 *
 * Extends EntityTransitionState for size/visibility transitions.
 * sizeIdx represents zoom level (0=horizon/smallest, max=foreground/largest).
 *
 * frameIdx: Current animation frame.
 * direction: Animation direction (1=forward, -1=backward).
 * worldX: World X position for scrolling.
 */
export interface TreeState extends EntityTransitionState {
    frameIdx: number;
    direction: number;
    worldX: number;
}
/**
 * Create initial tree state.
 *
 * Starts at second-largest visible size. The last size is the fade-out size,
 * so we use sizeCount - 3 to start one step back from the largest visible.
 *
 * Args:
 *     viewportWidth: Viewport width for initial positioning.
 *     sizeCount: Number of available tree sizes (including fade-out size).
 *
 * Returns:
 *     TreeState with initial values.
 */
export declare function createInitialTreeState(viewportWidth: number, sizeCount?: number): TreeState;
/**
 * Create animation timer for tree.
 *
 * Args:
 *     state: Tree state to animate.
 *     sizes: Available tree sizes.
 *     intervalMs: Animation interval in milliseconds.
 *
 * Returns:
 *     AnimationTimer for ping-pong animation.
 */
export declare function createTreeTimer(state: TreeState, sizes: TreeSize[], intervalMs: number): AnimationTimer;
/**
 * Get current tree frame.
 *
 * Args:
 *     state: Tree state.
 *     sizes: Available tree sizes.
 *
 * Returns:
 *     Frame data with lines and width, or null if invalid.
 */
export declare function getTreeFrame(state: TreeState, sizes: TreeSize[]): {
    lines: string[];
    width: number;
} | null;
/**
 * Get frames for size transition animation.
 *
 * Args:
 *     state: Tree state.
 *     sizes: Available tree sizes.
 *
 * Returns:
 *     Current and target frames with target index, or null if invalid.
 */
export declare function getTreeTransitionFrames(state: TreeState, sizes: TreeSize[]): {
    current: {
        lines: string[];
        width: number;
    };
    target: {
        lines: string[];
        width: number;
    };
    targetIdx: number;
} | null;
//# sourceMappingURL=Tree.d.ts.map