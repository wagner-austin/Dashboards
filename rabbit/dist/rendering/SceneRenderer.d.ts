/**
 * Scene renderer - handles frame-by-frame rendering of the entire scene.
 *
 * Coordinates layers, entities, ground, and scroll updates.
 */
import { type ViewportState } from "./Viewport.js";
import { type BunnyFrames, type BunnyState } from "../entities/Bunny.js";
import { type SceneState } from "../layers/index.js";
import { type Camera, type ProjectionConfig } from "../world/Projection.js";
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
 * Draw the bunny standing on the ground plane at his own depth.
 *
 * He is projected exactly as layer sprites are — feet on the ground point for
 * BUNNY_LAYER — rather than pinned to the bottom edge of the viewport. Pinning
 * placed him below every projected tree base, so no tree could overlap him
 * vertically and depth ordering alone could never occlude him.
 *
 * Horizontally he stays put: the camera tracks him, so his world X is the
 * camera's X and he projects to the same screen column every frame.
 *
 * Args:
 *     buffer: Render buffer.
 *     bunnyState: Bunny state.
 *     bunnyFrames: Bunny animation frames.
 *     camera: Current camera position.
 *     width: Buffer width.
 *     height: Buffer height.
 *     config: Projection configuration.
 *
 * Raises:
 *     Error: BUNNY_LAYER projects outside the visible band for this config, so
 *         the bunny cannot be drawn. Not recovered from: the alternative is
 *         silently drawing him at the top of the screen, and a scene whose
 *         subject is unplaceable is a configuration bug, not a frame to skip.
 */
declare function drawBunny(buffer: string[][], bunnyState: BunnyState, bunnyFrames: BunnyFrames, camera: Camera, width: number, height: number, config: ProjectionConfig): void;
/**
 * Depth the bunny occupies, in world units.
 *
 * Args:
 *     camera: Current camera position.
 *
 * Returns:
 *     World Z for the bunny. Constant, since the camera only advances in Z
 *     during a hop and the bunny hops with it.
 */
declare function bunnyWorldZ(camera: Camera): number;
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
    BUNNY_LAYER: number;
    bunnyWorldZ: typeof bunnyWorldZ;
    drawBunny: typeof drawBunny;
    renderFrame: typeof renderFrame;
};
export {};
//# sourceMappingURL=SceneRenderer.d.ts.map