/**
 * Keyboard input handling.
 */
import type { BunnyState, BunnyFrames, BunnyTimers } from "../entities/Bunny.js";
import type { TreeState, TreeSize } from "../entities/Tree.js";
import type { ViewportState } from "../rendering/Viewport.js";
export interface InputState {
    bunny: BunnyState;
    tree: TreeState;
    viewport: ViewportState;
    groundScrollX: number;
}
export declare function setupKeyboardControls(state: InputState, bunnyFrames: BunnyFrames, bunnyTimers: BunnyTimers, treeSizes: TreeSize[]): void;
//# sourceMappingURL=Keyboard.d.ts.map