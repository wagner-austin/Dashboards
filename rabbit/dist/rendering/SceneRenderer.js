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
 * Args:
 *     state: Current render state.
 *     bunnyFrames: Bunny animation frames.
 *     screen: Target pre element.
 *     currentTime: Current timestamp.
 *
 * Returns:
 *     Updated lastTime.
 */
export function renderFrame(state, bunnyFrames, screen, currentTime) {
    const { width, height } = state.viewport;
    const buffer = createBuffer(width, height);
    const config = state.projectionConfig;
    // Render background layers (includes trees via 3D projection)
    renderAllLayers(buffer, state.sceneState, width, height, config);
    // Draw ground using camera position
    drawGround(buffer, -Math.floor(state.sceneState.camera.x), width, height);
    // Draw bunny at fixed screen position
    drawBunny(buffer, state.bunnyState, bunnyFrames, width, height);
    // Render foreground layers
    renderForegroundLayers(buffer, state.sceneState, width, height, config);
    // Render to screen
    screen.textContent = renderBuffer(buffer);
    return { lastTime: currentTime };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    drawBunny,
    renderFrame,
};
//# sourceMappingURL=SceneRenderer.js.map