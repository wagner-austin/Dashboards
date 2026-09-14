/**
 * Scene renderer - handles frame-by-frame rendering of the entire scene.
 *
 * Coordinates layers, entities, ground, and scroll updates.
 */

import { createBuffer, renderBuffer, type ViewportState } from "./Viewport.js";
import { drawSprite } from "./draw.js";
import { drawGround } from "./Ground.js";
import { occludeStackedBuffers, type LayerBuffers } from "./occlusion.js";
import type { LayerColors } from "./colors.js";
import { getBunnyFrame, type BunnyFrames, type BunnyState } from "../entities/Bunny.js";
import { renderAllLayers, renderForegroundLayers, type SceneState } from "../layers/index.js";
import type { ProjectionConfig } from "../world/Projection.js";
import { project } from "../world/Projection.js";
import type { AdventureVisual } from "../entities/Adventure.js";
import { companionFrame } from "../entities/Companion.js";
import { blankCoveredCells } from "./occlusion.js";

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
  readonly adventure: AdventureVisual | null;
  bunnyState: BunnyState;
  sceneState: SceneState;
  viewport: ViewportState;
  lastTime: number;
  projectionConfig: ProjectionConfig;
}

/**
 * The three stacked <pre> elements the scene draws into.
 *
 * The scene used to render into a single element, which meant every glyph on
 * screen carried one CSS colour. Splitting it in three lets the actor be
 * coloured independently without the buffer having to hold a colour per cell
 * and without putting innerHTML on the 60fps path.
 *
 * Draw order is preserved by DOM stacking order: world, then actor, then
 * foreground. Draw order is NOT occlusion, though - these elements have no
 * background, so a glyph is transparent everywhere its ink is not and two
 * layers writing one cell are both painted. occludeStackedBuffers resolves
 * that in the buffers before they are emitted; see occlusion.ts.
 *
 * world: Background layers, trees, and the ground.
 * actor: The character, and nothing else.
 * foreground: Layers drawn in front of the actor.
 */
export interface ScreenLayers {
  readonly companion: HTMLPreElement;
  readonly world: HTMLPreElement;
  readonly actor: HTMLPreElement;
  readonly foreground: HTMLPreElement;
}

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
function drawBunny(
  buffer: string[][],
  bunnyState: BunnyState,
  bunnyFrames: BunnyFrames,
  width: number,
  height: number
): void {
  const bunny = getBunnyFrame(bunnyState, bunnyFrames);
  const spriteWidth = Math.max(0, ...bunny.lines.map((line) => line.length));
  const bunnyX = Math.floor((width - spriteWidth) / 2);
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
export function renderFrame(
  state: RenderState,
  bunnyFrames: BunnyFrames,
  layers: ScreenLayers,
  currentTime: number
): { lastTime: number } {
  const { width, height } = state.viewport;
  const config = state.projectionConfig;

  const buffers: LayerBuffers = {
    world: createBuffer(width, height),
    actor: createBuffer(width, height),
    foreground: createBuffer(width, height),
  };
  const companionBuffer = createBuffer(width, height);

  // Render background layers (includes trees via 3D projection)
  renderAllLayers(buffers.world, state.sceneState, width, height, config);

  // Draw ground using camera position
  drawGround(buffers.world, -Math.floor(state.sceneState.camera.x), width, height);

  // Draw bunny at fixed screen position, alone on its own layer
  if (state.adventure !== null && state.adventure.alert !== null) {
    const lines = state.adventure.alert;
    const spriteWidth = Math.max(...lines.map((line) => line.length));
    drawSprite(buffers.actor, lines, Math.floor((width - spriteWidth) / 2), height - lines.length - 2, width, height);
  } else {
    drawBunny(buffers.actor, state.bunnyState, bunnyFrames, width, height);
  }
  if (state.adventure !== null) {
    const visual = state.adventure;
    const camera = state.sceneState.camera;
    const position = project(camera.x + visual.companion.x,
      camera.z + config.nearZ + Math.max(0, visual.companion.z), camera, width, height, config);
    if (position.visible) {
      const lines = companionFrame(visual.companion, visual.assets.companion, visual.companionSprint);
      const scaled = scaleCharacter(lines, position.scale / (config.focalLength / config.nearZ));
      const baseline = project(camera.x, camera.z + config.nearZ, camera, width, height, config);
      const spriteWidth = Math.max(...scaled.map((line) => line.length));
      drawSprite(companionBuffer, scaled, position.x - Math.floor(spriteWidth / 2),
        height - scaled.length - 2 + position.y - baseline.y, width, height);
    }
    layers.companion.style.color = visual.companionColor;
  }

  // Render foreground layers
  renderForegroundLayers(buffers.foreground, state.sceneState, width, height, config);

  // Resolve the overlap the split created: a nearer layer's glyph must erase
  // the one behind it, which a shared buffer got from overwriting and stacked
  // transparent elements do not get at all.
  occludeStackedBuffers(buffers);
  blankCoveredCells(companionBuffer, buffers.foreground);
  blankCoveredCells(companionBuffer, buffers.actor);
  blankCoveredCells(buffers.world, companionBuffer);

  // Render to screen
  layers.world.textContent = renderBuffer(buffers.world);
  layers.actor.textContent = renderBuffer(buffers.actor);
  layers.foreground.textContent = renderBuffer(buffers.foreground);
  layers.companion.textContent = renderBuffer(companionBuffer);

  return { lastTime: currentTime };
}

/** Resample a rectangular character canvas while preserving its margins. */
function scaleCharacter(lines: readonly string[], scale: number): readonly string[] {
  const sourceWidth = Math.max(...lines.map((line) => line.length));
  const targetWidth = Math.max(1, Math.round(sourceWidth * scale));
  const targetHeight = Math.max(1, Math.round(lines.length * scale));
  return Array.from({ length: targetHeight }, (_, row) => {
    const source = lines[Math.floor(row * lines.length / targetHeight)];
    if (source === undefined) throw new Error("RABBIT_SPRITE_EMPTY: Character canvas has no rows.");
    const padded = source.padEnd(sourceWidth, " ");
    return Array.from({ length: targetWidth }, (_, col) => padded.charAt(Math.floor(col * sourceWidth / targetWidth))).join("");
  });
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
export function applyLayerColors(layers: ScreenLayers, colors: LayerColors): void {
  layers.world.style.color = colors.world;
  layers.actor.style.color = colors.actor;
  layers.foreground.style.color = colors.foreground;
}

/** Test hooks for internal functions */
export const _test_hooks = {
  scaleCharacter,
  drawBunny,
  renderFrame,
  applyLayerColors,
};
