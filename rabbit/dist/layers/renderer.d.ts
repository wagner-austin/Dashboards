/**
 * Layer rendering functions.
 *
 * Renders all layers using 3D projection to buffer.
 * Handles entity wrapping for infinite scrolling.
 */
import type { SceneState, LayerInstance, SceneSpriteState } from "./types.js";
import type { Camera, ProjectionConfig, ScreenPosition } from "../world/Projection.js";
/**
 * Wrap entity position for infinite scrolling.
 *
 * When entity is more than half world width from camera, wraps it
 * to the other side. Mutates entity.worldX in place.
 *
 * Args:
 *     entity: Entity to wrap.
 *     cameraX: Current camera X position.
 */
declare function wrapEntityPosition(entity: SceneSpriteState, cameraX: number): void;
/**
 * Project entity to screen and update its size index.
 *
 * Args:
 *     entity: Scene sprite to project.
 *     camera: Current camera position.
 *     viewportWidth: Screen width in characters.
 *     viewportHeight: Screen height in characters.
 *     config: Projection configuration.
 *
 * Returns:
 *     ScreenPosition with projected coordinates.
 */
declare function projectEntity(entity: SceneSpriteState, camera: Camera, viewportWidth: number, viewportHeight: number, config: ProjectionConfig): ScreenPosition;
/**
 * Render a single layer to buffer.
 *
 * Projects all entities in the layer and draws them at their screen positions.
 *
 * Args:
 *     buffer: 2D character buffer to draw into.
 *     layer: Layer instance containing entities.
 *     camera: Current camera position.
 *     viewportWidth: Screen width in characters.
 *     viewportHeight: Screen height in characters.
 *     config: Projection configuration.
 */
export declare function renderLayer(buffer: string[][], layer: LayerInstance, camera: Camera, viewportWidth: number, viewportHeight: number, config: ProjectionConfig): void;
/**
 * Render all background layers (excludes foreground layers).
 *
 * Layers with "front" in name are considered foreground and skipped.
 *
 * Args:
 *     buffer: 2D character buffer to draw into.
 *     scene: Scene state with camera and layers.
 *     viewportWidth: Screen width in characters.
 *     viewportHeight: Screen height in characters.
 *     config: Projection configuration.
 */
export declare function renderAllLayers(buffer: string[][], scene: SceneState, viewportWidth: number, viewportHeight: number, config: ProjectionConfig): void;
/**
 * Render tiled foreground layer with infinite wrapping.
 *
 * Args:
 *     buffer: 2D character buffer to draw into.
 *     entity: First entity in tiled layer.
 *     camera: Current camera position.
 *     viewportWidth: Screen width in characters.
 *     viewportHeight: Screen height in characters.
 */
declare function renderTiledForeground(buffer: string[][], entity: SceneSpriteState, camera: Camera, viewportWidth: number, viewportHeight: number): void;
/**
 * Render a foreground layer at projected Y position.
 *
 * For tiled layers, wraps tiles infinitely across viewport.
 *
 * Args:
 *     buffer: 2D character buffer to draw into.
 *     layer: Layer instance to render.
 *     camera: Current camera position.
 *     viewportWidth: Screen width in characters.
 *     viewportHeight: Screen height in characters.
 *     config: Projection configuration.
 */
export declare function renderForegroundLayer(buffer: string[][], layer: LayerInstance, camera: Camera, viewportWidth: number, viewportHeight: number, config: ProjectionConfig): void;
/**
 * Render all foreground layers (layers with "front" in name).
 *
 * Rendered after main entities so they appear in front.
 *
 * Args:
 *     buffer: 2D character buffer to draw into.
 *     scene: Scene state with camera and layers.
 *     viewportWidth: Screen width in characters.
 *     viewportHeight: Screen height in characters.
 *     config: Projection configuration.
 */
export declare function renderForegroundLayers(buffer: string[][], scene: SceneState, viewportWidth: number, viewportHeight: number, config: ProjectionConfig): void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    wrapEntityPosition: typeof wrapEntityPosition;
    projectEntity: typeof projectEntity;
    renderLayer: typeof renderLayer;
    renderForegroundLayer: typeof renderForegroundLayer;
    renderTiledForeground: typeof renderTiledForeground;
    WORLD_WIDTH: number;
};
export {};
//# sourceMappingURL=renderer.d.ts.map