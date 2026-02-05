/**
 * Layer rendering functions.
 * Renders all layers with parallax to buffer.
 */

import type { SceneState, LayerInstance, SceneSpriteState } from "./types.js";
import { drawSprite } from "../rendering/draw.js";
import { getSceneSpriteFrame, calculateSceneSpriteY } from "../entities/SceneSprite.js";

/**
 * Calculate screen X position with parallax applied.
 *
 * parallax = 0.0 → Fixed (doesn't move with camera)
 * parallax = 1.0 → Full movement (moves 1:1 with camera)
 */
export function getParallaxX(
  entityX: number,
  cameraX: number,
  parallax: number
): number {
  return entityX - Math.floor(cameraX * parallax);
}

/**
 * Render a single layer to buffer.
 * Applies parallax offset to all entities in layer.
 */
export function renderLayer(
  buffer: string[][],
  layer: LayerInstance,
  cameraX: number,
  viewportWidth: number,
  viewportHeight: number
): void {
  const parallax = layer.config.parallax;

  for (const entity of layer.entities) {
    const frame = getSceneSpriteFrame(entity);
    if (frame === null) {
      continue;
    }

    const screenX = getParallaxX(entity.x, cameraX, parallax);
    const screenY = calculateSceneSpriteY(entity, viewportHeight);

    drawSprite(buffer, frame.lines, screenX, screenY, viewportWidth, viewportHeight);
  }
}

/**
 * Render all background layers (excludes foreground layers).
 * Layers with "front" in name are considered foreground.
 */
export function renderAllLayers(
  buffer: string[][],
  scene: SceneState,
  viewportWidth: number,
  viewportHeight: number
): void {
  for (const layer of scene.layers) {
    if (!layer.config.name.includes("front")) {
      renderLayer(buffer, layer, scene.cameraX, viewportWidth, viewportHeight);
    }
  }
}

/**
 * Render tiled foreground layer with infinite wrapping.
 * Renders the first entity's frame repeated across viewport width.
 */
function renderTiledForeground(
  buffer: string[][],
  entity: SceneSpriteState,
  cameraX: number,
  parallax: number,
  viewportWidth: number,
  viewportHeight: number
): void {
  const frame = getSceneSpriteFrame(entity);
  if (frame === null) return;

  const tileWidth = frame.width;
  const screenY = viewportHeight - frame.lines.length;

  // Calculate starting X based on camera, wrapping to tile boundary
  const parallaxOffset = Math.floor(cameraX * parallax);
  const startX = -(parallaxOffset % tileWidth);

  // Render enough tiles to fill viewport
  for (let x = startX - tileWidth; x < viewportWidth + tileWidth; x += tileWidth) {
    drawSprite(buffer, frame.lines, x, screenY, viewportWidth, viewportHeight);
  }
}

/**
 * Render a foreground layer at the bottom of the screen.
 * Used for sprites that should appear in front of other entities.
 * For tiled layers, wraps tiles infinitely.
 */
export function renderForegroundLayer(
  buffer: string[][],
  layer: LayerInstance,
  cameraX: number,
  viewportWidth: number,
  viewportHeight: number
): void {
  const parallax = layer.config.parallax;
  const isTiled = layer.config.tile;
  const firstEntity = layer.entities[0];

  if (isTiled && firstEntity !== undefined) {
    // For tiled layers, render tiles that wrap infinitely
    renderTiledForeground(buffer, firstEntity, cameraX, parallax, viewportWidth, viewportHeight);
  } else {
    // Non-tiled: render each entity at its position
    for (const entity of layer.entities) {
      const frame = getSceneSpriteFrame(entity);
      if (frame === null) {
        continue;
      }

      const screenX = getParallaxX(entity.x, cameraX, parallax);
      const screenY = viewportHeight - frame.lines.length;

      drawSprite(buffer, frame.lines, screenX, screenY, viewportWidth, viewportHeight);
    }
  }
}

/**
 * Render all foreground layers (layers with "front" in name).
 * Positioned at bottom of screen, rendered after main entities.
 */
export function renderForegroundLayers(
  buffer: string[][],
  scene: SceneState,
  viewportWidth: number,
  viewportHeight: number
): void {
  for (const layer of scene.layers) {
    if (layer.config.name.includes("front")) {
      renderForegroundLayer(buffer, layer, scene.cameraX, viewportWidth, viewportHeight);
    }
  }
}

/** Test hooks for internal functions */
export const _test_hooks = {
  getParallaxX,
  renderLayer,
  renderForegroundLayer,
  renderTiledForeground,
};
