/**
 * Scene renderer - handles frame-by-frame rendering of the entire scene.
 * Coordinates layers, entities, ground, and scroll updates.
 */
import { type ViewportState } from "./Viewport.js";
import { type BunnyFrames, type BunnyState } from "../entities/Bunny.js";
import { type TreeSize, type TreeState } from "../entities/Tree.js";
import { type SceneState } from "../layers/index.js";
/** Render state for a single frame */
export interface RenderState {
    bunnyState: BunnyState;
    treeState: TreeState;
    sceneState: SceneState;
    viewport: ViewportState;
    groundScrollX: number;
    lastTime: number;
}
/** Render a single frame - pure function for testability */
export declare function renderFrame(state: RenderState, bunnyFrames: BunnyFrames, treeSizes: TreeSize[], screen: HTMLPreElement, currentTime: number, scrollSpeed: number, transitionDurationMs: number): {
    groundScrollX: number;
    lastTime: number;
};
//# sourceMappingURL=SceneRenderer.d.ts.map