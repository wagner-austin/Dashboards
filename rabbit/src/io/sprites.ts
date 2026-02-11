/**
 * Sprite loading I/O code.
 * This module contains dynamic imports which require browser/bundler integration.
 * Excluded from unit test coverage - testability ensured through dependency injection.
 */

import type { Config, FrameSet } from "../types.js";
import type { BunnyFrames } from "../entities/Bunny.js";
import type { TreeSize } from "../entities/Tree.js";
import type { ValidatedLayer } from "../layers/types.js";
import type { SpriteRegistry } from "../loaders/layers.js";
import type {
  MutableSpriteRegistry,
  ProgressCallback,
} from "../loaders/progressive.js";
import {
  collectTreeWidths,
  getGrassSpriteNames,
  getTreeSpriteNames,
  getSpriteWidthsFromConfig,
  getOrCreateSpriteArray,
  insertSortedByWidth,
} from "../loaders/progressive.js";
import { _test_hooks as spritesHooks } from "../loaders/sprites.js";

const { validateSpriteModule } = spritesHooks;

/** Module interface for sprite frame exports */
export interface SpriteModule {
  readonly frames: readonly string[];
}

/** Cache for loaded sprite modules to prevent duplicate downloads */
const spriteModuleCache = new Map<string, Promise<SpriteModule>>();

/** Dynamic import with validation and caching */
async function importSpriteModule(path: string): Promise<SpriteModule> {
  // Check cache first
  const cached = spriteModuleCache.get(path);
  if (cached !== undefined) {
    return cached;
  }

  // Create promise and cache it immediately to handle concurrent requests
  const promise = (async (): Promise<SpriteModule> => {
    const module: unknown = await import(/* @vite-ignore */ path);
    return validateSpriteModule(module, path);
  })();

  spriteModuleCache.set(path, promise);
  return promise;
}

/**
 * Load sprite frames for animated sprites (with direction).
 */
export async function loadSpriteFrames(
  spriteName: string,
  animationName: string,
  width: number,
  direction?: string
): Promise<FrameSet> {
  const suffix = direction !== undefined ? `_${direction}` : "";
  const path = `../sprites/${spriteName}/${animationName}/w${String(width)}${suffix}.js`;
  const module = await importSpriteModule(path);
  return {
    width,
    frames: module.frames,
  };
}

/**
 * Load sprite frames for static sprites (no direction).
 */
export async function loadStaticSpriteFrames(
  spriteName: string,
  width: number
): Promise<FrameSet> {
  const path = `../sprites/${spriteName}/w${String(width)}.js`;
  const module = await importSpriteModule(path);
  return {
    width,
    frames: module.frames,
  };
}

/**
 * Load config from JSON file.
 */
export async function loadConfig(): Promise<Config> {
  const { validateConfig } = spritesHooks;
  const response = await fetch("./config.json");
  const data: unknown = await response.json();
  return validateConfig(data);
}

/**
 * Load bunny animation frames (directional).
 */
async function loadDirectionalFrames(
  animation: string,
  width: number
): Promise<{ left: readonly string[]; right: readonly string[] }> {
  const [left, right] = await Promise.all([
    loadSpriteFrames("bunny", animation, width, "left"),
    loadSpriteFrames("bunny", animation, width, "right"),
  ]);
  return { left: left.frames, right: right.frames };
}

/**
 * Load bunny animation frames (single direction).
 */
async function loadSingleFrames(animation: string, width: number): Promise<readonly string[]> {
  const result = await loadSpriteFrames("bunny", animation, width);
  return result.frames;
}

/**
 * Load all bunny animation frames.
 */
export async function loadBunnyFrames(_config: Config): Promise<BunnyFrames> {
  const [walk, jump, idle, walkToIdle, walkToTurnAway, walkToTurnToward, hopAway, hopToward] = await Promise.all([
    loadDirectionalFrames("walk", 50),
    loadDirectionalFrames("jump", 50),
    loadDirectionalFrames("idle", 40),
    loadDirectionalFrames("walk_to_idle", 40),
    loadDirectionalFrames("walk_to_turn_away", 40),
    loadDirectionalFrames("walk_to_turn_toward", 40),
    loadSingleFrames("hop_away", 40),
    loadSingleFrames("hop_toward", 40),
  ]);

  return {
    walkLeft: walk.left,
    walkRight: walk.right,
    jumpLeft: jump.left,
    jumpRight: jump.right,
    idleLeft: idle.left,
    idleRight: idle.right,
    walkToIdleLeft: walkToIdle.left,
    walkToIdleRight: walkToIdle.right,
    walkToTurnAwayLeft: walkToTurnAway.left,
    walkToTurnAwayRight: walkToTurnAway.right,
    walkToTurnTowardLeft: walkToTurnToward.left,
    walkToTurnTowardRight: walkToTurnToward.right,
    hopAway,
    hopToward,
  };
}

/**
 * Load all tree size variations from config.
 *
 * Reads tree sprite widths from config and loads each size.
 * Returns sizes sorted smallest to largest.
 *
 * Args:
 *     config: Application config with sprite definitions.
 *
 * Returns:
 *     Array of TreeSize sorted by width ascending.
 */
export async function loadTreeSizes(config: Config): Promise<TreeSize[]> {
  const { getSpriteWidths } = await import("../loaders/layers.js");
  const widths = getSpriteWidths(config, "tree1");
  const sizes: TreeSize[] = [];
  for (const w of widths) {
    const set = await loadStaticSpriteFrames("tree1", w);
    sizes.push({ width: w, frames: set.frames });
  }
  return sizes;
}

/**
 * Load all sprites referenced by layers.
 */
export async function loadLayerSprites(
  config: Config,
  layers: readonly ValidatedLayer[]
): Promise<SpriteRegistry> {
  const { getSpriteWidths } = await import("../loaders/layers.js");
  const sprites = new Map<string, readonly FrameSet[]>();

  // Collect unique sprite names from all layers
  const spriteNames = new Set<string>();
  for (const layer of layers) {
    for (const name of layer.spriteNames) {
      spriteNames.add(name);
    }
  }

  // Load each sprite's frames at all widths
  for (const name of spriteNames) {
    const widths = getSpriteWidths(config, name);
    const sizes: FrameSet[] = [];

    for (const width of widths) {
      const frameSet = await loadStaticSpriteFrames(name, width);
      sizes.push(frameSet);
    }

    sprites.set(name, sizes);
  }

  return { sprites };
}

/**
 * Load grass sprites into mutable registry.
 *
 * Args:
 *     config: Application config.
 *     registry: Mutable sprite registry.
 *     onProgress: Progress callback.
 */
export async function loadGrassSprites(
  config: Config,
  registry: MutableSpriteRegistry,
  onProgress: ProgressCallback
): Promise<void> {
  const grassNames = getGrassSpriteNames(config);
  let current = 0;
  let total = 0;

  // Count total widths to load
  for (const name of grassNames) {
    const widths = getSpriteWidthsFromConfig(config, name);
    total += widths.length;
  }

  for (const name of grassNames) {
    const widths = getSpriteWidthsFromConfig(config, name);
    const sizes = getOrCreateSpriteArray(registry, name);

    for (const width of widths) {
      current++;
      onProgress({ phase: "grass", current, total, spriteName: name, width });

      const frameSet = await loadStaticSpriteFrames(name, width);
      insertSortedByWidth(sizes, frameSet);
    }
  }
}

/**
 * Load tree sprites progressively from largest to smallest.
 *
 * Loads trees interleaved across tree types (tree1, tree2, etc.)
 * so that the largest trees from all types load first.
 *
 * Args:
 *     config: Application config.
 *     registry: Mutable sprite registry.
 *     onProgress: Progress callback.
 */
export async function loadTreeSpritesProgressive(
  config: Config,
  registry: MutableSpriteRegistry,
  onProgress: ProgressCallback
): Promise<void> {
  const treeNames = getTreeSpriteNames(config);
  const entries = collectTreeWidths(config, treeNames);
  const total = entries.length;

  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];
    if (entry === undefined) continue;

    const { spriteName, width } = entry;
    onProgress({ phase: "trees", current: i + 1, total, spriteName, width });

    const sizes = getOrCreateSpriteArray(registry, spriteName);
    const frameSet = await loadStaticSpriteFrames(spriteName, width);
    insertSortedByWidth(sizes, frameSet);
  }
}

/**
 * Callback invoked when bunny frames finish loading.
 */
export type BunnyLoadedCallback = (frames: BunnyFrames) => void;

/**
 * Run progressive loading sequence.
 *
 * Loads sprites in order: ground, grass, bunny, trees (largest to smallest).
 * Calls onProgress for each loaded sprite to enable UI updates.
 * Calls onBunnyLoaded immediately when bunny frames are ready, before trees.
 *
 * Args:
 *     config: Application config.
 *     registry: Mutable sprite registry to populate.
 *     onProgress: Progress callback for each loaded sprite.
 *     onBunnyLoaded: Callback when bunny frames are ready (before trees load).
 */
export async function runProgressiveLoad(
  config: Config,
  registry: MutableSpriteRegistry,
  onProgress: ProgressCallback,
  onBunnyLoaded: BunnyLoadedCallback
): Promise<void> {
  // Phase 1: Ground (instant - notify only)
  onProgress({ phase: "ground", current: 1, total: 1, spriteName: "ground", width: 0 });

  // Phase 2: Grass sprites
  await loadGrassSprites(config, registry, onProgress);

  // Phase 3: Bunny frames - notify immediately when ready
  onProgress({ phase: "bunny", current: 1, total: 1, spriteName: "bunny", width: 50 });
  const bunnyFrames = await loadBunnyFrames(config);
  onBunnyLoaded(bunnyFrames);

  // Phase 4: Trees (largest to smallest)
  await loadTreeSpritesProgressive(config, registry, onProgress);
}
