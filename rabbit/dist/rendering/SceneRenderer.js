/**
 * Scene renderer - handles frame-by-frame rendering of the entire scene.
 *
 * Coordinates layers, entities, ground, and scroll updates.
 */
import { createBuffer, renderBuffer } from "./Viewport.js";
import { drawSprite } from "./draw.js";
import { drawGround } from "./Ground.js";
import { getBunnyFrame, isWalking } from "../entities/Bunny.js";
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
 * Handles layer rendering, bunny drawing, ground scrolling, and camera updates.
 * Trees are rendered via the layer system with 3D projection.
 *
 * Args:
 *     state: Current render state.
 *     bunnyFrames: Bunny animation frames.
 *     screen: Target pre element.
 *     currentTime: Current timestamp.
 *     scrollSpeed: Base scroll speed.
 *
 * Returns:
 *     Updated lastTime.
 */
export function renderFrame(state, bunnyFrames, screen, currentTime, scrollSpeed) {
    const deltaTime = state.lastTime > 0 ? (currentTime - state.lastTime) / 1000 : 0;
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
    // Update camera position when walking
    if (isWalking(state.bunnyState)) {
        const scrollAmount = scrollSpeed * deltaTime;
        const direction = state.bunnyState.facingRight ? 1 : -1;
        state.sceneState.camera = {
            ...state.sceneState.camera,
            x: state.sceneState.camera.x + scrollAmount * direction,
        };
    }
    return { lastTime: currentTime };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    drawBunny,
    renderFrame,
};
//# sourceMappingURL=SceneRenderer.js.map