/**
 * Shared fixtures for the io/ suites.
 *
 * Kept apart from fixtures.ts, which serves the input layer: these build
 * config documents and layer definitions, and the two sets have no overlap.
 * Every io suite needs the same complete character config, and duplicating it
 * five times is how the copies drift.
 */

import { DEFAULT_AUTORUN_CONFIG } from "../input/index.js";
import type { Config, SpriteAnimationConfig } from "../types.js";
import type { ValidatedLayer } from "../layers/types.js";

/**
 * Build one animation entry.
 *
 * Args:
 *     directional: Whether to declare left and right, which is what makes
 *         generate_sprites.py emit `_left`/`_right` filenames.
 *     width: The single width the animation declares.
 *
 * Returns:
 *     The animation config entry.
 */
export function createTestAnimation(
  directional: boolean,
  width: number
): SpriteAnimationConfig {
  return {
    source: "originals/x.gif",
    widths: [width],
    contrast: 1.4,
    invert: true,
    ...(directional ? { directions: ["left", "right"] as const } : {}),
  };
}

/**
 * Build a complete animations block for a character.
 *
 * Every animation the state machine drives, shaped the way the resolver
 * requires: six directional, and the two depth hops undirected.
 *
 * Returns:
 *     The animations block.
 */
export function createTestAnimations(): Record<string, SpriteAnimationConfig> {
  return {
    walk: createTestAnimation(true, 50),
    jump: createTestAnimation(true, 50),
    idle: createTestAnimation(true, 40),
    walk_to_idle: createTestAnimation(true, 40),
    walk_to_turn_away: createTestAnimation(true, 40),
    walk_to_turn_toward: createTestAnimation(true, 40),
    hop_away: createTestAnimation(false, 40),
    hop_toward: createTestAnimation(false, 40),
  };
}

/**
 * Build a config with a loadable character plus scenery.
 *
 * Args:
 *     characters: Character names to include, each with a complete
 *         animations block.
 *
 * Returns:
 *     A config the io loaders can run against end to end.
 */
export function createTestConfig(characters: readonly string[] = ["bunny"]): Config {
  const sprites: Record<string, Config["sprites"][string]> = {
    tree1: { source: "t1.gif", widths: [15, 40] },
    tree2: { source: "t2.gif", widths: [15, 40] },
    grass: { source: "g.mp4", widths: [160] },
  };
  for (const name of characters) {
    sprites[name] = { animations: createTestAnimations() };
  }

  return {
    sprites,
    layers: [{ name: "grass-front", sprites: ["grass"], layer: 6, tile: true }],
    settings: {
      fps: 60,
      scrollSpeed: 90,
      depthSpeed: 30,
      animation: { walk: 120, idle: 500, jump: 58, transition: 85, hop: 150 },
    },
    autorun: DEFAULT_AUTORUN_CONFIG,
    autoLayers: {
      sprites: ["tree1", "tree2"],
      minLayer: 9,
      maxLayer: 30,
      treesPerLayer: 2,
      seed: 42,
    },
  };
}

/**
 * Build a validated layer naming the given sprites.
 *
 * Args:
 *     name: Layer name.
 *     spriteNames: Sprites the layer draws.
 *
 * Returns:
 *     A ValidatedLayer suitable for loadLayerSprites.
 */
export function createTestValidatedLayer(
  name: string,
  spriteNames: readonly string[]
): ValidatedLayer {
  return {
    name,
    type: "tile",
    layer: 6,
    spriteNames,
    positions: [0],
    zIndex: 6,
    tile: true,
    behavior: { parallax: 1, wrapX: true, wrapZ: false },
  };
}
