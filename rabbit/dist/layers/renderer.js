/**
 * Layer rendering functions.
 *
 * Renders all layers using 3D projection to buffer.
 * Handles entity wrapping for infinite scrolling.
 */
import { project, scaleToSizeIndex } from "../world/Projection.js";
import { drawSprite } from "../rendering/draw.js";
import { getSceneSpriteFrame } from "../entities/SceneSprite.js";
/** World width for entity wrapping */
const WORLD_WIDTH = 800;
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
function projectEntity(entity, camera, viewportWidth, viewportHeight, config) {
    const screen = project(entity.worldX, entity.worldZ, camera, viewportWidth, viewportHeight, config);
    if (screen.visible) {
        entity.sizeIdx = scaleToSizeIndex(screen.scale, entity.sizes.length);
    }
    return screen;
}
/**
 * Render a single layer to buffer.
 *
 * Projects all entities in the layer and draws them at their screen positions.
 * Uses layer behavior to determine wrapping.
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
    // Use behavior-based wrapping (tiled layers handle their own repetition)
    const shouldWrapX = layer.config.behavior.wrapX && !layer.config.tile;
    for (const entity of layer.entities) {
        if (shouldWrapX) {
            wrapEntityPosition(entity, camera.x);
        }
        const screen = projectEntity(entity, camera, viewportWidth, viewportHeight, config);
        if (!screen.visible) {
            continue;
        }
        const frame = getSceneSpriteFrame(entity);
        if (frame === null) {
            continue;
        }
        const spriteX = screen.x - Math.floor(frame.width / 2);
        const spriteY = screen.y - frame.lines.length;
        drawSprite(buffer, frame.lines, spriteX, spriteY, viewportWidth, viewportHeight);
    }
}
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
export function renderAllLayers(buffer, scene, viewportWidth, viewportHeight, config) {
    for (const layer of scene.layers) {
        if (!layer.config.name.includes("front")) {
            renderLayer(buffer, layer, scene.camera, viewportWidth, viewportHeight, config);
        }
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
        for (const entity of layer.entities) {
            const screen = projectEntity(entity, camera, viewportWidth, viewportHeight, config);
            if (!screen.visible) {
                continue;
            }
            const frame = getSceneSpriteFrame(entity);
            if (frame === null) {
                continue;
            }
            const spriteX = screen.x - Math.floor(frame.width / 2);
            const spriteY = screen.y - frame.lines.length;
            drawSprite(buffer, frame.lines, spriteX, spriteY, viewportWidth, viewportHeight);
        }
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
    projectEntity,
    renderLayer,
    renderForegroundLayer,
    renderTiledForeground,
    WORLD_WIDTH,
};
//# sourceMappingURL=renderer.js.map