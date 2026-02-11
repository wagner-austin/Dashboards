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
 * Load all bunny animation frames.
 */
export async function loadBunnyFrames(_config: Config): Promise<BunnyFrames> {
  const [walkLeft, walkRight, jumpLeft, jumpRight, idleLeft, idleRight, walkToIdleLeft, walkToIdleRight] = await Promise.all([
    loadSpriteFrames("bunny", "walk", 50, "left"),
    loadSpriteFrames("bunny", "walk", 50, "right"),
    loadSpriteFrames("bunny", "jump", 50, "left"),
    loadSpriteFrames("bunny", "jump", 50, "right"),
    loadSpriteFrames("bunny", "idle", 40, "left"),
    loadSpriteFrames("bunny", "idle", 40, "right"),
    loadSpriteFrames("bunny", "walk_to_idle", 40, "left"),
    loadSpriteFrames("bunny", "walk_to_idle", 40, "right"),
  ]);

  return {
    walkLeft: walkLeft.frames,
    walkRight: walkRight.frames,
    jumpLeft: jumpLeft.frames,
    jumpRight: jumpRight.frames,
    idleLeft: idleLeft.frames,
    idleRight: idleRight.frames,
    walkToIdleLeft: walkToIdleLeft.frames,
    walkToIdleRight: walkToIdleRight.frames,
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
