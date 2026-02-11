/**
 * Progressive sprite loading for scene population.
 *
 * Loads sprites in a controlled order to populate scene progressively:
 * 1. Ground (instant - pure ASCII)
 * 2. Grass sprites
 * 3. Bunny animation frames
 * 4. Trees from largest to smallest width
 */

import type { Config, FrameSet } from "../types.js";

/**
 * Load phase for progressive loading.
 *
 * ground: ASCII ground (instant).
 * grass: Grass sprite widths.
 * bunny: All bunny animation frames.
 * trees: Tree widths from largest to smallest.
 */
export type LoadPhase = "ground" | "grass" | "bunny" | "trees";

/**
 * Tree width entry for ordered loading.
 *
 * spriteName: Name of tree sprite (tree1 or tree2).
 * width: Width to load.
 */
export interface TreeWidthEntry {
  readonly spriteName: string;
  readonly width: number;
}

/**
 * Progress update for loading callbacks.
 *
 * phase: Current load phase.
 * current: Current item index within phase.
 * total: Total items in phase.
 * spriteName: Name of sprite being loaded.
 * width: Width being loaded (for sprites with widths).
 */
export interface LoadProgress {
  readonly phase: LoadPhase;
  readonly current: number;
  readonly total: number;
  readonly spriteName: string;
  readonly width: number;
}

/**
 * Callback for load progress updates.
 */
export type ProgressCallback = (progress: LoadProgress) => void;

/**
 * Mutable sprite registry for progressive loading.
 *
 * Holds mutable FrameSet arrays that can be populated incrementally.
 * Entities hold references to these arrays and see new frames as they load.
 */
export interface MutableSpriteRegistry {
  readonly sprites: Map<string, FrameSet[]>;
}

/**
 * Create empty mutable sprite registry.
 *
 * Args:
 *     spriteNames: Names of sprites to create entries for.
 *
 * Returns:
 *     MutableSpriteRegistry with empty arrays for each sprite.
 */
export function createMutableSpriteRegistry(
  spriteNames: readonly string[]
): MutableSpriteRegistry {
  const sprites = new Map<string, FrameSet[]>();
  for (const name of spriteNames) {
    sprites.set(name, []);
  }
  return { sprites };
}

/**
 * Get or create sprite array in registry.
 *
 * Args:
 *     registry: Mutable sprite registry.
 *     spriteName: Name of sprite.
 *
 * Returns:
 *     Mutable FrameSet array for the sprite.
 */
export function getOrCreateSpriteArray(
  registry: MutableSpriteRegistry,
  spriteName: string
): FrameSet[] {
  const existing = registry.sprites.get(spriteName);
  if (existing !== undefined) {
    return existing;
  }
  const newArray: FrameSet[] = [];
  registry.sprites.set(spriteName, newArray);
  return newArray;
}

/**
 * Insert frame set into sorted position by width.
 *
 * Maintains ascending width order in the array.
 *
 * Args:
 *     sizes: Mutable array of frame sets.
 *     frameSet: Frame set to insert.
 */
export function insertSortedByWidth(sizes: FrameSet[], frameSet: FrameSet): void {
  let insertIdx = 0;
  for (let i = 0; i < sizes.length; i++) {
    const current = sizes[i];
    if (current !== undefined && current.width < frameSet.width) {
      insertIdx = i + 1;
    } else {
      break;
    }
  }
  sizes.splice(insertIdx, 0, frameSet);
}

/**
 * Collect all tree widths from config, sorted descending (largest first).
 *
 * Combines widths from all tree sprites and returns unique widths
 * with their sprite names, sorted by width descending.
 *
 * Args:
 *     config: Application config with sprite definitions.
 *     treeNames: Names of tree sprites to collect widths from.
 *
 * Returns:
 *     Array of TreeWidthEntry sorted by width descending.
 */
export function collectTreeWidths(
  config: Config,
  treeNames: readonly string[]
): readonly TreeWidthEntry[] {
  const entries: TreeWidthEntry[] = [];

  for (const spriteName of treeNames) {
    const spriteConfig = config.sprites[spriteName];
    if (spriteConfig === undefined) {
      continue;
    }

    const widths = spriteConfig.widths;
    if (widths === undefined) {
      continue;
    }

    for (const width of widths) {
      entries.push({ spriteName, width });
    }
  }

  // Sort by width descending (largest first)
  entries.sort((a, b) => b.width - a.width);

  return entries;
}

/**
 * Get grass sprite names from config layers.
 *
 * Args:
 *     config: Application config with layer definitions.
 *
 * Returns:
 *     Array of grass sprite names.
 */
export function getGrassSpriteNames(config: Config): readonly string[] {
  const grassNames: string[] = [];

  for (const layer of config.layers) {
    if (layer.sprites !== undefined) {
      for (const spriteName of layer.sprites) {
        if (spriteName.includes("grass")) {
          grassNames.push(spriteName);
        }
      }
    }
  }

  return grassNames;
}

/**
 * Get tree sprite names from autoLayers config.
 *
 * Args:
 *     config: Application config with autoLayers.
 *
 * Returns:
 *     Array of tree sprite names, or empty if no autoLayers.
 */
export function getTreeSpriteNames(config: Config): readonly string[] {
  if (config.autoLayers === undefined) {
    return [];
  }
  return config.autoLayers.sprites;
}

/**
 * Get sprite widths from config.
 *
 * Args:
 *     config: Application config.
 *     spriteName: Name of sprite.
 *
 * Returns:
 *     Array of widths, or empty if sprite not found.
 */
export function getSpriteWidthsFromConfig(
  config: Config,
  spriteName: string
): readonly number[] {
  const spriteConfig = config.sprites[spriteName];
  if (spriteConfig === undefined) {
    return [];
  }
  return spriteConfig.widths ?? [];
}

/** Test hooks for internal functions. */
export const _test_hooks = {
  createMutableSpriteRegistry,
  getOrCreateSpriteArray,
  insertSortedByWidth,
  collectTreeWidths,
  getGrassSpriteNames,
  getTreeSpriteNames,
  getSpriteWidthsFromConfig,
};
