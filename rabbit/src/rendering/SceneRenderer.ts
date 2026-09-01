/**
 * Scene renderer - handles frame-by-frame rendering of the entire scene.
 *
 * Coordinates layers, entities, ground, and scroll updates.
 */

import { createBuffer, renderBuffer, type ViewportState } from "./Viewport.js";
import { drawSprite } from "./draw.js";
import { drawGround } from "./Ground.js";
import { getBunnyFrame, type BunnyFrames, type BunnyState } from "../entities/Bunny.js";
import { renderAllLayers, renderForegroundLayers, type SceneState } from "../layers/index.js";
import { layerToWorldZ } from "../layers/widths.js";
import {
  project,
  DEFAULT_CAMERA_Z,
  type Camera,
  type ProjectionConfig,
} from "../world/Projection.js";

/**
 * Layer the bunny stands on.
 *
 * Two invariants ride on this value, and both were broken before it existed:
 *
 * 1. It must sit inside the visible band. Projection discards anything closer
 *    than `nearZ` (40) from the camera (55), so worldZ below 95 — layer 9 — is
 *    never drawn. A bunny below that could not be occluded by any tree, since
 *    the trees that would cover him would themselves be clipped.
 * 2. Trees between layer 9 and this value render in front of him, so the value
 *    also sets how much of the forest can pass between him and the viewer.
 *
 * Layer 10 leaves only layer 9 rendering in front of him, and puts him one
 * step nearer the camera than 11 did. Layer 9 is the clip plane, so this is
 * one short of as far forward as he can go while anything can still pass in
 * front; reaching 9 itself would leave nothing nearer than him, and going
 * nearer than 9 needs `nearZ` widened, which rescales the whole scene.
 * `SceneRenderer.test.ts` asserts both directions against a real frame.
 */
const BUNNY_LAYER = 10;

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
 * Draw the bunny standing on the ground plane at his own depth.
 *
 * He is projected exactly as layer sprites are — feet on the ground point for
 * BUNNY_LAYER — rather than pinned to the bottom edge of the viewport. Pinning
 * placed him below every projected tree base, so no tree could overlap him
 * vertically and depth ordering alone could never occlude him.
 *
 * Horizontally he stays put: the camera tracks him, so his world X is the
 * camera's X and he projects to the same screen column every frame.
 *
 * Args:
 *     buffer: Render buffer.
 *     bunnyState: Bunny state.
 *     bunnyFrames: Bunny animation frames.
 *     camera: Current camera position.
 *     width: Buffer width.
 *     height: Buffer height.
 *     config: Projection configuration.
 *
 * Raises:
 *     Error: BUNNY_LAYER projects outside the visible band for this config, so
 *         the bunny cannot be drawn. Not recovered from: the alternative is
 *         silently drawing him at the top of the screen, and a scene whose
 *         subject is unplaceable is a configuration bug, not a frame to skip.
 */
function drawBunny(
  buffer: string[][],
  bunnyState: BunnyState,
  bunnyFrames: BunnyFrames,
  camera: Camera,
  width: number,
  height: number,
  config: ProjectionConfig
): void {
  const bunny = getBunnyFrame(bunnyState, bunnyFrames);
  const worldZ = bunnyWorldZ(camera);
  const screen = project(camera.x, worldZ, camera, width, height, config);
  if (!screen.visible) {
    throw new Error(
      `BUNNY_UNPLACEABLE: bunny at layer ${String(BUNNY_LAYER)} projects to ` +
        `worldZ ${String(worldZ)}, which is ${String(worldZ - camera.z)} from the ` +
        `camera and outside the visible band [${String(config.nearZ)}, ` +
        `${String(config.farZ)}]. Move BUNNY_LAYER inside it.`
    );
  }
  const bunnyX = Math.floor(width / 2) - 20;
  drawSprite(buffer, bunny.lines, bunnyX, screen.y - bunny.lines.length, width, height);
}

/**
 * Depth the bunny occupies, in world units.
 *
 * Args:
 *     camera: Current camera position.
 *
 * Returns:
 *     World Z for the bunny. Constant, since the camera only advances in Z
 *     during a hop and the bunny hops with it.
 */
function bunnyWorldZ(camera: Camera): number {
  return layerToWorldZ(BUNNY_LAYER) + camera.z - DEFAULT_CAMERA_Z;
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
export function renderFrame(
  state: RenderState,
  bunnyFrames: BunnyFrames,
  screen: HTMLPreElement,
  currentTime: number
): { lastTime: number } {
  const { width, height } = state.viewport;
  const buffer = createBuffer(width, height);
  const config = state.projectionConfig;

  const bunnyZ = bunnyWorldZ(state.sceneState.camera);

  // Background layers behind the bunny (includes trees via 3D projection)
  renderAllLayers(buffer, state.sceneState, width, height, config, {
    minZ: bunnyZ,
    maxZ: Number.POSITIVE_INFINITY,
  });

  // Draw ground using camera position
  drawGround(buffer, -Math.floor(state.sceneState.camera.x), width, height);

  // Draw the bunny on the ground plane at his own depth
  drawBunny(
    buffer,
    state.bunnyState,
    bunnyFrames,
    state.sceneState.camera,
    width,
    height,
    config
  );

  // Background layers NEARER than the bunny, so they draw over him.
  renderAllLayers(buffer, state.sceneState, width, height, config, {
    minZ: Number.NEGATIVE_INFINITY,
    maxZ: bunnyZ,
  });

  // Render foreground layers
  renderForegroundLayers(buffer, state.sceneState, width, height, config);

  // Render to screen
  screen.textContent = renderBuffer(buffer);

  return { lastTime: currentTime };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  BUNNY_LAYER,
  bunnyWorldZ,
  drawBunny,
  renderFrame,
};
