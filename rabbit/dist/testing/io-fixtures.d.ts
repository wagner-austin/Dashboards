/**
 * Shared fixtures for the io/ suites.
 *
 * Kept apart from fixtures.ts, which serves the input layer: these build
 * config documents and layer definitions, and the two sets have no overlap.
 * Every io suite needs the same complete character config, and duplicating it
 * five times is how the copies drift.
 */
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
export declare function createTestAnimation(directional: boolean, width: number): SpriteAnimationConfig;
/**
 * Build a complete animations block for a character.
 *
 * Every animation the state machine drives, shaped the way the resolver
 * requires: six directional, and the two depth hops undirected.
 *
 * Returns:
 *     The animations block.
 */
export declare function createTestAnimations(): Record<string, SpriteAnimationConfig>;
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
export declare function createTestConfig(characters?: readonly string[]): Config;
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
export declare function createTestValidatedLayer(name: string, spriteNames: readonly string[]): ValidatedLayer;
//# sourceMappingURL=io-fixtures.d.ts.map