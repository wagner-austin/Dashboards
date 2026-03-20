/**
 * Layer rendering functions.
 *
 * Renders all layers using 3D projection to buffer.
 * Handles entity wrapping for infinite scrolling.
 */
import { createRenderCandidate } from "./types.js";
import { project, scaleToSizeIndex, WORLD_WIDTH } from "../world/Projection.js";
import { drawSprite } from "../rendering/draw.js";
import { getSceneSpriteFrame } from "../entities/SceneSprite.js";
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
function wrapEntityPosition(entity, cameraX) {
    const relativeX = entity.worldX - cameraX;
    const halfWorld = WORLD_WIDTH / 2;
    if (relativeX < -halfWorld) {
        entity.worldX += WORLD_WIDTH;
    }
    else if (relativeX > halfWorld) {
        entity.worldX -= WORLD_WIDTH;
    }
}
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
function getWrappedZPositions(worldZ, config) {
    const visibleDepth = config.farZ - config.nearZ;
    const positions = [];
    for (let i = config.wrapIterations; i >= -config.wrapIterations; i--) {
        positions.push(worldZ + i * visibleDepth);
    }
    return positions;
}
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
function collectWrappedCandidates(entities, config) {
    const candidates = [];
    for (const entity of entities) {
        const zPositions = getWrappedZPositions(entity.worldZ, config);
        for (const effectiveZ of zPositions) {
            candidates.push(createRenderCandidate(entity, effectiveZ));
        }
    }
    return candidates;
}
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
function collectDirectCandidates(entities) {
    const candidates = [];
    for (const entity of entities) {
        candidates.push(createRenderCandidate(entity, entity.worldZ));
    }
    return candidates;
}
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
function compareByDepth(a, b) {
    return b.effectiveZ - a.effectiveZ;
}
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
function renderCandidate(buffer, candidate, camera, viewportWidth, viewportHeight, config) {
    renderEntityAtZ(buffer, candidate.entity, candidate.effectiveZ, camera, viewportWidth, viewportHeight, config);
}
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
function renderEntitiesDepthSorted(buffer, entities, camera, viewportWidth, viewportHeight, config, shouldWrapZ) {
    const candidates = shouldWrapZ
        ? collectWrappedCandidates(entities, config)
        : collectDirectCandidates(entities);
    candidates.sort(compareByDepth);
    for (const candidate of candidates) {
        renderCandidate(buffer, candidate, camera, viewportWidth, viewportHeight, config);
    }
}
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
function renderEntityAtZ(buffer, entity, worldZ, camera, viewportWidth, viewportHeight, config) {
    const screen = project(entity.worldX, worldZ, camera, viewportWidth, viewportHeight, config);
    if (!screen.visible) {
        return;
    }
    // Update sizeIdx based on projection scale
    entity.sizeIdx = scaleToSizeIndex(screen.scale, entity.sizes.length);
    const frame = getSceneSpriteFrame(entity);
    if (frame === null) {
        return;
    }
    const spriteX = screen.x - Math.floor(frame.width / 2);
    const spriteY = screen.y - frame.lines.length;
    drawSprite(buffer, frame.lines, spriteX, spriteY, viewportWidth, viewportHeight);
}
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
export function renderLayer(buffer, layer, camera, viewportWidth, viewportHeight, config) {
    const shouldWrapX = layer.config.behavior.wrapX && !layer.config.tile;
    const shouldWrapZ = layer.config.behavior.wrapZ;
    if (shouldWrapX) {
        for (const entity of layer.entities) {
            wrapEntityPosition(entity, camera.x);
        }
    }
    renderEntitiesDepthSorted(buffer, layer.entities, camera, viewportWidth, viewportHeight, config, shouldWrapZ);
}
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
function collectLayerCandidates(layer, camera, config) {
    const shouldWrapX = layer.config.behavior.wrapX && !layer.config.tile;
    const shouldWrapZ = layer.config.behavior.wrapZ;
    if (shouldWrapX) {
        for (const entity of layer.entities) {
            wrapEntityPosition(entity, camera.x);
        }
    }
    return shouldWrapZ
        ? collectWrappedCandidates(layer.entities, config)
        : collectDirectCandidates(layer.entities);
}
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
export function renderAllLayers(buffer, scene, viewportWidth, viewportHeight, config) {
    const allCandidates = [];
    for (const layer of scene.layers) {
        if (!layer.config.name.includes("front")) {
            const candidates = collectLayerCandidates(layer, scene.camera, config);
            allCandidates.push(...candidates);
        }
    }
    allCandidates.sort(compareByDepth);
    for (const candidate of allCandidates) {
        renderCandidate(buffer, candidate, scene.camera, viewportWidth, viewportHeight, config);
    }
}
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
function renderTiledForeground(buffer, entity, camera, viewportWidth, viewportHeight) {
    const frame = getSceneSpriteFrame(entity);
    if (frame === null) {
        return;
    }
    const tileWidth = frame.width;
    // Fixed Y at bottom of viewport (ground layer)
    const screenY = viewportHeight - frame.lines.length;
    // No parallax - moves 1:1 with camera
    const offset = Math.floor(camera.x);
    const startX = -(offset % tileWidth);
    // Render enough tiles to fill viewport
    for (let x = startX - tileWidth; x < viewportWidth + tileWidth; x += tileWidth) {
        drawSprite(buffer, frame.lines, x, screenY, viewportWidth, viewportHeight);
    }
}
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
export function renderForegroundLayer(buffer, layer, camera, viewportWidth, viewportHeight, config) {
    const isTiled = layer.config.tile;
    const firstEntity = layer.entities[0];
    if (isTiled && firstEntity !== undefined) {
        renderTiledForeground(buffer, firstEntity, camera, viewportWidth, viewportHeight);
    }
    else {
        renderEntitiesDepthSorted(buffer, layer.entities, camera, viewportWidth, viewportHeight, config, layer.config.behavior.wrapZ);
    }
}
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
export function renderForegroundLayers(buffer, scene, viewportWidth, viewportHeight, config) {
    for (const layer of scene.layers) {
        if (layer.config.name.includes("front")) {
            renderForegroundLayer(buffer, layer, scene.camera, viewportWidth, viewportHeight, config);
        }
    }
}
/** Test hooks for internal functions */
export const _test_hooks = {
    wrapEntityPosition,
    getWrappedZPositions,
    renderEntityAtZ,
    renderEntitiesDepthSorted,
    renderLayer,
    renderForegroundLayer,
    renderTiledForeground,
    collectWrappedCandidates,
    collectDirectCandidates,
    compareByDepth,
    renderCandidate,
    collectLayerCandidates,
};
//# sourceMappingURL=renderer.js.map