/**
 * Layer rendering functions.
 * Renders all layers with parallax to buffer.
 */
import type { SceneState, LayerInstance, SceneSpriteState } from "./types.js";
/**
 * Calculate screen X position with parallax applied.
 *
 * parallax = 0.0 → Fixed (doesn't move with camera)
 * parallax = 1.0 → Full movement (moves 1:1 with camera)
 */
export declare function getParallaxX(entityX: number, cameraX: number, parallax: number): number;
/**
 * Render a single layer to buffer.
 * Applies parallax offset to all entities in layer.
 */
export declare function renderLayer(buffer: string[][], layer: LayerInstance, cameraX: number, viewportWidth: number, viewportHeight: number): void;
/**
 * Render all background layers (excludes foreground layers).
 * Layers with "front" in name are considered foreground.
 */
export declare function renderAllLayers(buffer: string[][], scene: SceneState, viewportWidth: number, viewportHeight: number): void;
/**
 * Render tiled foreground layer with infinite wrapping.
 * Renders the first entity's frame repeated across viewport width.
 */
declare function renderTiledForeground(buffer: string[][], entity: SceneSpriteState, cameraX: number, parallax: number, viewportWidth: number, viewportHeight: number): void;
/**
 * Render a foreground layer at the bottom of the screen.
 * Used for sprites that should appear in front of other entities.
 * For tiled layers, wraps tiles infinitely.
 */
export declare function renderForegroundLayer(buffer: string[][], layer: LayerInstance, cameraX: number, viewportWidth: number, viewportHeight: number): void;
/**
 * Render all foreground layers (layers with "front" in name).
 * Positioned at bottom of screen, rendered after main entities.
 */
export declare function renderForegroundLayers(buffer: string[][], scene: SceneState, viewportWidth: number, viewportHeight: number): void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    getParallaxX: typeof getParallaxX;
    renderLayer: typeof renderLayer;
    renderForegroundLayer: typeof renderForegroundLayer;
    renderTiledForeground: typeof renderTiledForeground;
};
export {};
//# sourceMappingURL=renderer.d.ts.map