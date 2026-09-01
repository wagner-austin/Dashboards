/**
 * Scene renderer - handles frame-by-frame rendering of the entire scene.
 *
 * Coordinates layers, entities, ground, and scroll updates.
 */
import { type ViewportState } from "./Viewport.js";
import { type BunnyFrames, type BunnyState } from "../entities/Bunny.js";
import { type SceneState } from "../layers/index.js";
import type { ProjectionConfig } from "../world/Projection.js";
/**
 * Render state for a single frame.
 *
 * bunnyState: Current bunny animation state.
 * sceneState: Scene with layers and camera.
 * viewport: Screen dimensions.
 * lastTime: Timestamp of previous frame.
 * projectionConfig: 3D projection settings for layers.
 */
export interface RenderState {
    bunnyState: BunnyState;
    sceneState: SceneState;
    viewport: ViewportState;
    lastTime: number;
    projectionConfig: ProjectionConfig;
}
/**
 * Draw the bunny entity to buffer.
 *
 * Args:
 *     buffer: Render buffer.
 *     bunnyState: Bunny state.
 *     bunnyFrames: Bunny animation frames.
 *     width: Buffer width.
 *     height: Buffer height.
 */
declare function drawBunny(buffer: string[][], bunnyState: BunnyState, bunnyFrames: BunnyFrames, width: number, height: number): void;
/**
 * Render a single frame.
 *
 * Draws only: layers, ground, bunny, foreground. Moving the camera belongs to
 * the input layer's movement module, which is its sole writer - rendering used
 * to pan it too, so the two speeds silently added together.
 *
 * Args:
 *     state: Current render state.
 *     bunnyFrames: Bunny animation frames.
 *     screen: Target pre element.
 *     currentTime: Current timestamp.
 *
 * Returns:
 *     Updated lastTime.
 */
export declare function renderFrame(state: RenderState, bunnyFrames: BunnyFrames, screen: HTMLPreElement, currentTime: number): {
    lastTime: number;
};
/** Test hooks for internal functions */
export declare const _test_hooks: {
    drawBunny: typeof drawBunny;
    renderFrame: typeof renderFrame;
};
export {};
//# sourceMappingURL=SceneRenderer.d.ts.map