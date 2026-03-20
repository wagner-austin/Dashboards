/**
 * Layer rendering functions.
 *
 * Renders all layers using 3D projection to buffer.
 * Handles entity wrapping for infinite scrolling.
 */
import type { SceneState, LayerInstance, SceneSpriteState, RenderCandidate } from "./types.js";
import type { Camera, ProjectionConfig } from "../world/Projection.js";
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
 * Get wrapped Z positions for seamless infinite depth scrolling.
 *
 * Wraps at visible depth intervals (farZ - nearZ) so wrapped copies
 * appear in the distance before originals disappear behind camera.
 *
 * Args:
 *     worldZ: Entity's actual world Z position.
 *     config: Projection config (visible depth = farZ - nearZ).
 *
 * Returns:
 *     Array of Z positions from back to front (highest Z first).
 */
declare function getWrappedZPositions(worldZ: number, config: ProjectionConfig): readonly number[];
/**
 * Collect render candidates for a layer with Z wrapping.
 *
 * Gathers all entity/effectiveZ pairs that might be visible.
 * Each entity generates multiple candidates at wrapped Z positions.
 *
 * Args:
 *     entities: Entities to collect candidates from.
 *     config: Projection config for visible depth calculation.
 *
 * Returns:
 *     Array of render candidates.
 */
declare function collectWrappedCandidates(entities: readonly SceneSpriteState[], config: ProjectionConfig): RenderCandidate[];
/**
 * Collect render candidates for a layer without Z wrapping.
 *
 * Each entity generates a single candidate at its actual Z position.
 *
 * Args:
 *     entities: Entities to collect candidates from.
 *
 * Returns:
 *     Array of render candidates.
 */
declare function collectDirectCandidates(entities: readonly SceneSpriteState[]): RenderCandidate[];
/**
 * Compare render candidates by depth (back to front).
 *
 * Higher effectiveZ values sort first (farther from camera).
 * This ensures proper overdraw order when rendering.
 *
 * Args:
 *     a: First candidate.
 *     b: Second candidate.
 *
 * Returns:
 *     Negative if a should render first, positive if b should render first.
 */
declare function compareByDepth(a: RenderCandidate, b: RenderCandidate): number;
/**
 * Render a single candidate to buffer.
 *
 * Projects entity at the effective Z position and draws if visible.
 *
 * Args:
 *     buffer: 2D character buffer to draw into.
 *     candidate: Render candidate with entity and effectiveZ.
 *     camera: Current camera position.
 *     viewportWidth: Screen width in characters.
 *     viewportHeight: Screen height in characters.
 *     config: Projection configuration.
 */
declare function renderCandidate(buffer: string[][], candidate: RenderCandidate, camera: Camera, viewportWidth: number, viewportHeight: number, config: ProjectionConfig): void;
/**
 * Render entities with depth-sorted ordering.
 *
 * Collects candidates (with optional Z wrapping), sorts by depth,
 * and renders back to front for correct overdraw.
 *
 * Args:
 *     buffer: 2D character buffer to draw into.
 *     entities: Entities to render.
 *     camera: Current camera position.
 *     viewportWidth: Screen width in characters.
 *     viewportHeight: Screen height in characters.
 *     config: Projection configuration.
 *     shouldWrapZ: Whether to generate wrapped Z positions.
 */
declare function renderEntitiesDepthSorted(buffer: string[][], entities: readonly SceneSpriteState[], camera: Camera, viewportWidth: number, viewportHeight: number, config: ProjectionConfig, shouldWrapZ: boolean): void;
/**
 * Render entity at a specific world Z position.
 *
 * Projects entity to screen and draws if visible.
 *
 * Args:
 *     buffer: 2D character buffer to draw into.
 *     entity: Scene sprite to render.
 *     worldZ: World Z position to render at.
 *     camera: Current camera position.
 *     viewportWidth: Screen width in characters.
 *     viewportHeight: Screen height in characters.
 *     config: Projection configuration.
 */
declare function renderEntityAtZ(buffer: string[][], entity: SceneSpriteState, worldZ: number, camera: Camera, viewportWidth: number, viewportHeight: number, config: ProjectionConfig): void;
/**
 * Render a single layer to buffer.
 *
 * Projects all entities in the layer and draws them at their screen positions.
 * For Z-wrapping layers, collects all render candidates, sorts by depth
 * (back to front), and renders in sorted order for correct overdraw.
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
 * Collect candidates from a layer with X wrapping applied.
 *
 * Applies X wrapping to entities if layer behavior requires it,
 * then collects render candidates (with or without Z wrapping).
 *
 * Args:
 *     layer: Layer instance to collect from.
 *     camera: Current camera position.
 *     config: Projection configuration.
 *
 * Returns:
 *     Array of render candidates from this layer.
 */
declare function collectLayerCandidates(layer: LayerInstance, camera: Camera, config: ProjectionConfig): RenderCandidate[];
/**
 * Render all background layers with global depth sorting.
 *
 * Collects ALL candidates from ALL non-front layers, sorts globally
 * by depth (back to front), then renders in one pass. This ensures
 * correct z-ordering across all layers.
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
 * For non-tiled layers, uses depth-sorted rendering for correct overdraw.
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
    getWrappedZPositions: typeof getWrappedZPositions;
    renderEntityAtZ: typeof renderEntityAtZ;
    renderEntitiesDepthSorted: typeof renderEntitiesDepthSorted;
    renderLayer: typeof renderLayer;
    renderForegroundLayer: typeof renderForegroundLayer;
    renderTiledForeground: typeof renderTiledForeground;
    collectWrappedCandidates: typeof collectWrappedCandidates;
    collectDirectCandidates: typeof collectDirectCandidates;
    compareByDepth: typeof compareByDepth;
    renderCandidate: typeof renderCandidate;
    collectLayerCandidates: typeof collectLayerCandidates;
};
export {};
//# sourceMappingURL=renderer.d.ts.map