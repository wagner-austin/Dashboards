/**
 * Assembling one character's animation frames.
 *
 * Which character, and the width of each of its animations, come from
 * config.json by way of loaders/character.ts. Nothing here names a specific
 * character, so a second one needs config and art rather than a code change.
 */
import type { Config } from "../types.js";
import type { BunnyFrames } from "../entities/Bunny.js";
import { type AnimationSource } from "../loaders/character.js";
/**
 * Load one animation's frames, directional or not.
 *
 * Args:
 *     character: Character sprite name.
 *     source: The animation's resolved width and directions.
 *
 * Returns:
 *     Left and right frame lists for a directional animation; for an
 *     undirected one, the single list under both keys, which is what the two
 *     depth hops want — they face away from and toward the camera, so there
 *     is no side to pick.
 */
declare function loadAnimation(character: string, source: AnimationSource): Promise<{
    left: readonly string[];
    right: readonly string[];
}>;
/**
 * Load every animation frame for a character.
 *
 * Args:
 *     config: Application config.
 *     character: Character sprite name.
 *
 * Returns:
 *     The assembled BunnyFrames.
 *
 * Raises:
 *     Error: If config cannot supply the character's animations.
 */
export declare function loadCharacterFrames(config: Config, character: string): Promise<BunnyFrames>;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    loadAnimation: typeof loadAnimation;
};
export {};
//# sourceMappingURL=character-io.d.ts.map