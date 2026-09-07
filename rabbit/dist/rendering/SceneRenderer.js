/**
 * Scene renderer - handles frame-by-frame rendering of the entire scene.
 *
 * Coordinates layers, entities, ground, and scroll updates.
 */
import { createBuffer, renderBuffer } from "./Viewport.js";
import { drawSprite } from "./draw.js";
import { drawGround } from "./Ground.js";
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
    const worldBuffer = createBuffer(width, height);
    const actorBuffer = createBuffer(width, height);
    const foregroundBuffer = createBuffer(width, height);
    // Render background layers (includes trees via 3D projection)
    renderAllLayers(worldBuffer, state.sceneState, width, height, config);
    // Draw ground using camera position
    drawGround(worldBuffer, -Math.floor(state.sceneState.camera.x), width, height);
    // Draw bunny at fixed screen position, alone on its own layer
    drawBunny(actorBuffer, state.bunnyState, bunnyFrames, width, height);
    // Render foreground layers
    renderForegroundLayers(foregroundBuffer, state.sceneState, width, height, config);
    // Render to screen
    layers.world.textContent = renderBuffer(worldBuffer);
    layers.actor.textContent = renderBuffer(actorBuffer);
    layers.foreground.textContent = renderBuffer(foregroundBuffer);
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