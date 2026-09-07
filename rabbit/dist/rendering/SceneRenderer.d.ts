/**
 * Scene renderer - handles frame-by-frame rendering of the entire scene.
 *
 * Coordinates layers, entities, ground, and scroll updates.
 */
import { type ViewportState } from "./Viewport.js";
import type { LayerColors } from "./colors.js";
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
 * The three stacked <pre> elements the scene draws into.
 *
 * The scene used to render into a single element, which meant every glyph on
 * screen carried one CSS colour. Splitting it in three lets the actor be
 * coloured independently without the buffer having to hold a colour per cell
 * and without putting innerHTML on the 60fps path.
 *
 * Draw order is preserved by DOM stacking order: world, then actor, then
 * foreground. A space is transparent in all three, so occlusion works exactly
 * as it did when the layers shared one buffer - foreground grass still covers
 * the actor, and the actor still covers the trees.
 *
 * world: Background layers, trees, and the ground.
 * actor: The character, and nothing else.
 * foreground: Layers drawn in front of the actor.
 */
export interface ScreenLayers {
    readonly world: HTMLPreElement;
    readonly actor: HTMLPreElement;
    readonly foreground: HTMLPreElement;
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
 * Each of the three buffers is the full viewport grid, so all three elements
 * carry identical dimensions and stay aligned without any positioning
 * arithmetic. Cells no layer writes stay spaces, which are transparent.
 *
 * Args:
 *     state: Current render state.
 *     bunnyFrames: Bunny animation frames.
 *     layers: The three stacked target elements.
 *     currentTime: Current timestamp.
 *
 * Returns:
 *     Updated lastTime.
 */
export declare function renderFrame(state: RenderState, bunnyFrames: BunnyFrames, layers: ScreenLayers, currentTime: number): {
    lastTime: number;
};
/**
 * Apply layer colours to the three stacked elements.
 *
 * Called once at startup rather than per frame: the colours come from
 * config.json and nothing mutates them afterwards.
 *
 * Args:
 *     layers: The three stacked target elements.
 *     colors: Validated colours from the config's colours block.
 */
export declare function applyLayerColors(layers: ScreenLayers, colors: LayerColors): void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    drawBunny: typeof drawBunny;
    renderFrame: typeof renderFrame;
    applyLayerColors: typeof applyLayerColors;
};
export {};
//# sourceMappingURL=SceneRenderer.d.ts.map