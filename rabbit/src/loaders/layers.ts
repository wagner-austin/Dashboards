/**
 * Layer loading from config.
 *
 * Dynamically loads sprite frames based on config and creates
 * layer instances with entities at specified positions.
 */

import type { Config, FrameSet, TreeZoomConfig, LayerSpriteConfig } from "../types.js";
import type { ValidatedLayer, LayerInstance, SceneSpriteState } from "../layers/types.js";
import { createSceneSpriteState } from "../entities/SceneSprite.js";
import { layerToWorldZ, generateLayerWidths } from "../layers/widths.js";
import type { MutableSpriteRegistry } from "./progressive.js";
import { getOrCreateSpriteArray } from "./progressive.js";

/** Registry of loaded sprite frames by name (immutable for backwards compatibility) */
export interface SpriteRegistry {
  readonly sprites: ReadonlyMap<string, readonly FrameSet[]>;
}

/**
 * Calculate sprite widths from zoom config.
 *
 * Lerps between minWidth and maxWidth, creating steps+1 widths.
 * Rounds to integers for consistent sprite generation.
 *
 * Args:
 *     zoom: Tree zoom configuration.
 *
 * Returns:
 *     Array of widths from smallest (horizon) to largest (foreground).
 */
export function calculateZoomWidths(zoom: TreeZoomConfig): readonly number[] {
  const widths: number[] = [];
  for (let i = 0; i <= zoom.steps; i++) {
    const t = i / zoom.steps;
    const width = Math.round(zoom.minWidth + (zoom.maxWidth - zoom.minWidth) * t);
    widths.push(width);
  }
  return widths;
}

/**
 * Calculate sprite widths from layer config.
 *
 * Uses power curve for decreasing steps (fine at small end, coarse at large).
 *
 * Args:
 *     layerConfig: Layer sprite configuration.
 *
 * Returns:
 *     Array of widths from smallest to largest.
 */
export function calculateLayerWidths(layerConfig: LayerSpriteConfig): readonly number[] {
  return generateLayerWidths(layerConfig);
}

/**
 * Get sprite widths from config for a sprite name.
 *
 * Priority order:
 * 1. Explicit widths array
 * 2. First animation's widths
 * 3. Layer config (auto-calculated)
 * 4. Zoom config (legacy)
 *
 * Args:
 *     config: Application config.
 *     spriteName: Name of sprite to get widths for.
 *
 * Returns:
 *     Sorted array of available widths (smallest to largest).
 *
 * Raises:
 *     Error: If sprite not found or has no widths defined.
 */
export function getSpriteWidths(config: Config, spriteName: string): readonly number[] {
  const spriteConfig = config.sprites[spriteName];
  if (spriteConfig === undefined) {
    throw new Error(`Sprite "${spriteName}" not found in config`);
  }

  // Check for explicit widths first (preferred for loading actual sprite files)
  if (spriteConfig.widths !== undefined) {
    return [...spriteConfig.widths].sort((a, b) => a - b);
  }

  // Check for widths in first animation
  if (spriteConfig.animations !== undefined) {
    const animationKeys = Object.keys(spriteConfig.animations);
    const firstKey = animationKeys[0];
    if (firstKey !== undefined) {
      const firstAnim = spriteConfig.animations[firstKey];
      if (firstAnim !== undefined) {
        return [...firstAnim.widths].sort((a, b) => a - b);
      }
    }
  }

  // Check for layer config (new auto-calculated widths)
  if (spriteConfig.layerConfig !== undefined) {
    return calculateLayerWidths(spriteConfig.layerConfig);
  }

  // Fall back to zoom config (legacy auto-calculates widths)
  if (spriteConfig.zoom !== undefined) {
    return calculateZoomWidths(spriteConfig.zoom);
  }

  throw new Error(`Sprite "${spriteName}" has no widths defined`);
}

/**
 * Create layer instances from validated config.
 *
 * Instantiates entities based on layer configuration:
 * - If tile=true: tiles sprites across viewport with buffer
 * - If positions specified: creates entity at each position
 * - Otherwise: creates single centered entity
 *
 * Args:
 *     layers: Validated layer configurations.
 *     registry: Registry of loaded sprite frames.
 *     viewportWidth: Viewport width in characters.
 *
 * Returns:
 *     Array of layer instances with entities.
 *
 * Raises:
 *     Error: If sprite not found in registry.
 */
export function createLayerInstances(
  layers: readonly ValidatedLayer[],
  registry: SpriteRegistry,
  viewportWidth: number
): LayerInstance[] {
  const instances: LayerInstance[] = [];

  for (const config of layers) {
    const entities: SceneSpriteState[] = [];

    for (const spriteName of config.spriteNames) {
      const readonlySizes = registry.sprites.get(spriteName);
      if (readonlySizes === undefined) {
        throw new Error(`Sprite "${spriteName}" not found in registry`);
      }

      // Create mutable copy for progressive loading support
      const sizes: FrameSet[] = [...readonlySizes];

      const middleSizeIdx = Math.floor(sizes.length / 2);
      const spriteWidth = sizes[middleSizeIdx]?.width ?? 100;

      // Convert layer number to world Z coordinate
      const worldZ = layerToWorldZ(config.layer);

      if (config.tile) {
        // Create multiple entities to tile across viewport (plus buffer for scrolling)
        const tileBuffer = viewportWidth * 4;
        const totalWidth = viewportWidth + tileBuffer;
        const numTiles = Math.ceil(totalWidth / spriteWidth) + 1;
        const startX = -tileBuffer / 2;

        for (let i = 0; i < numTiles; i++) {
          const worldX = startX + i * spriteWidth;
          const entity = createSceneSpriteState(spriteName, sizes, worldX, worldZ, middleSizeIdx);
          entities.push(entity);
        }
      } else if (config.positions.length > 0) {
        // Create entity at each specified position
        for (const worldX of config.positions) {
          const entity = createSceneSpriteState(spriteName, sizes, worldX, worldZ, middleSizeIdx);
          entities.push(entity);
        }
      } else {
        // Create single entity centered in viewport
        const worldX = Math.floor(viewportWidth / 2);
        const entity = createSceneSpriteState(spriteName, sizes, worldX, worldZ, middleSizeIdx);
        entities.push(entity);
      }
    }

    instances.push({ config, entities });
  }

  return instances;
}

/**
 * Create layer instances with mutable sprite arrays for progressive loading.
 *
 * Creates entities that reference mutable size arrays from the registry.
 * As widths load, the entities see new sizes automatically.
 * Uses default sprite width (100) for tiling since actual widths not yet loaded.
 *
 * Args:
 *     layers: Validated layer configurations.
 *     registry: Mutable registry with sprite arrays.
 *     viewportWidth: Viewport width in characters.
 *
 * Returns:
 *     Array of layer instances with entities referencing mutable size arrays.
 */
export function createProgressiveLayerInstances(
  layers: readonly ValidatedLayer[],
  registry: MutableSpriteRegistry,
  viewportWidth: number
): LayerInstance[] {
  const instances: LayerInstance[] = [];

  for (const config of layers) {
    const entities: SceneSpriteState[] = [];

    for (const spriteName of config.spriteNames) {
      const sizes = getOrCreateSpriteArray(registry, spriteName);
      const worldZ = layerToWorldZ(config.layer);

      // Use default width for tiling since sizes may be empty
      const defaultSpriteWidth = 100;

      if (config.tile) {
        const tileBuffer = viewportWidth * 4;
        const totalWidth = viewportWidth + tileBuffer;
        const numTiles = Math.ceil(totalWidth / defaultSpriteWidth) + 1;
        const startX = -tileBuffer / 2;

        for (let i = 0; i < numTiles; i++) {
          const worldX = startX + i * defaultSpriteWidth;
          const entity = createSceneSpriteState(spriteName, sizes, worldX, worldZ, 0);
          entities.push(entity);
        }
      } else if (config.positions.length > 0) {
        for (const worldX of config.positions) {
          const entity = createSceneSpriteState(spriteName, sizes, worldX, worldZ, 0);
          entities.push(entity);
        }
      } else {
        const worldX = Math.floor(viewportWidth / 2);
        const entity = createSceneSpriteState(spriteName, sizes, worldX, worldZ, 0);
        entities.push(entity);
      }
    }

    instances.push({ config, entities });
  }

  return instances;
}

/** Test hooks for internal functions */
export const _test_hooks = {
  calculateZoomWidths,
  calculateLayerWidths,
  getSpriteWidths,
  createLayerInstances,
  createProgressiveLayerInstances,
};
