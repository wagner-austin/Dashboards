/**
 * Tree entity - state, zoom, and frame selection.
 */
import { type AnimationTimer } from "../loaders/sprites.js";
export interface TreeSize {
    width: number;
    frames: readonly string[];
}
export interface TreeState {
    frameIdx: number;
    direction: number;
    sizeIdx: number;
    targetSizeIdx: number;
    sizeTransitionProgress: number;
    centerX: number;
}
export declare function createInitialTreeState(viewportWidth: number): TreeState;
export declare function createTreeTimer(state: TreeState, sizes: TreeSize[], intervalMs: number): AnimationTimer;
export declare function calcTreeY(treeHeight: number, sizeIdx: number, viewportHeight: number): number;
export declare function getTreeFrame(state: TreeState, sizes: TreeSize[]): {
    lines: string[];
    width: number;
} | null;
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