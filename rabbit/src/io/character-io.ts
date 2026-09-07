/**
 * Assembling one character's animation frames.
 *
 * Which character, and the width of each of its animations, come from
 * config.json by way of loaders/character.ts. Nothing here names a specific
 * character, so a second one needs config and art rather than a code change.
 */

import type { Config } from "../types.js";
import type { BunnyFrames } from "../entities/Bunny.js";
import {
  resolveCharacterAnimations,
  type AnimationSource,
} from "../loaders/character.js";
import { loadSpriteFrames } from "./transport.js";

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
async function loadAnimation(
  character: string,
  source: AnimationSource
): Promise<{ left: readonly string[]; right: readonly string[] }> {
  if (source.directions === null) {
    const single = await loadSpriteFrames(character, source.animation, source.width);
    return { left: single.frames, right: single.frames };
  }
  const [left, right] = await Promise.all([
    loadSpriteFrames(character, source.animation, source.width, "left"),
    loadSpriteFrames(character, source.animation, source.width, "right"),
  ]);
  return { left: left.frames, right: right.frames };
}

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
export async function loadCharacterFrames(
  config: Config,
  character: string
): Promise<BunnyFrames> {
  const sources = resolveCharacterAnimations(config, character);
  const [
    walk,
    jump,
    idle,
    walkToIdle,
    walkToTurnAway,
    walkToTurnToward,
    hopAway,
    hopToward,
  ] = await Promise.all([
    loadAnimation(character, sources.walk),
    loadAnimation(character, sources.jump),
    loadAnimation(character, sources.idle),
    loadAnimation(character, sources.walkToIdle),
    loadAnimation(character, sources.walkToTurnAway),
    loadAnimation(character, sources.walkToTurnToward),
    loadAnimation(character, sources.hopAway),
    loadAnimation(character, sources.hopToward),
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
    hopAway: hopAway.left,
    hopToward: hopToward.left,
  };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  loadAnimation,
};
