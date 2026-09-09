/**
 * Scene renderer - handles frame-by-frame rendering of the entire scene.
 *
 * Coordinates layers, entities, ground, and scroll updates.
 */
import { createBuffer, renderBuffer } from "./Viewport.js";
import { drawSprite } from "./draw.js";
import { drawGround } from "./Ground.js";
import { occludeStackedBuffers } from "./occlusion.js";
import { getBunnyFrame } from "../entities/Bunny.js";
import { renderAllLayers, renderForegroundLayers } from "../layers/index.js";
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
function drawBunny(buffer, bunnyState, bunnyFrames, width, height) {
    const bunny = getBunnyFrame(bunnyState, bunnyFrames);
    const bunnyX = Math.floor(width / 2) - 20;
    const bunnyY = height - bunny.lines.length - 2;
    drawSprite(buffer, bunny.lines, bunnyX, bunnyY, width, height);
}
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
 * The buffers are drawn back to front and then occluded against each other,
 * because stacking three transparent elements reproduces draw order but not
 * overwrite: without that pass a cell written by two layers shows both glyphs
 * at once.
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
export function renderFrame(state, bunnyFrames, layers, currentTime) {
    const { width, height } = state.viewport;
    const config = state.projectionConfig;
    const buffers = {
        world: createBuffer(width, height),
        actor: createBuffer(width, height),
        foreground: createBuffer(width, height),
    };
    // Render background layers (includes trees via 3D projection)
    renderAllLayers(buffers.world, state.sceneState, width, height, config);
    // Draw ground using camera position
    drawGround(buffers.world, -Math.floor(state.sceneState.camera.x), width, height);
    // Draw bunny at fixed screen position, alone on its own layer
    drawBunny(buffers.actor, state.bunnyState, bunnyFrames, width, height);
    // Render foreground layers
    renderForegroundLayers(buffers.foreground, state.sceneState, width, height, config);
    // Resolve the overlap the split created: a nearer layer's glyph must erase
    // the one behind it, which a shared buffer got from overwriting and stacked
    // transparent elements do not get at all.
    occludeStackedBuffers(buffers);
    // Render to screen
    layers.world.textContent = renderBuffer(buffers.world);
    layers.actor.textContent = renderBuffer(buffers.actor);
    layers.foreground.textContent = renderBuffer(buffers.foreground);
    return { lastTime: currentTime };
}
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
export function applyLayerColors(layers, colors) {
    layers.world.style.color = colors.world;
    layers.actor.style.color = colors.actor;
    layers.foreground.style.color = colors.foreground;
}
/** Test hooks for internal functions */
export const _test_hooks = {
    drawBunny,
    renderFrame,
    applyLayerColors,
};
//# sourceMappingURL=SceneRenderer.js.map