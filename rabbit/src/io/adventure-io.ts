/** Load the additional sequences required by the two-character scene. */
import type { Config } from "../types.js";
import type { AdventureAssets } from "../entities/Adventure.js";
import { loadCharacterFrames } from "./character-io.js";
import { loadSpriteFrames } from "./transport.js";

/**
 * Load companion and upright frames through the shared sprite transport.
 *
 * Args:
 *   config: Validated application configuration.
 *   leader: The character controlled by the user.
 * Returns:
 *   Complete animation assets for the adventure service.
 * Raises:
 *   Error: RABBIT_CHARACTER when a character has no defined companion.
 *   Error: RABBIT_ALERT_CONFIG when upright frames are not configured.
 */
export async function loadAdventureAssets(config: Config, leader: string): Promise<AdventureAssets> {
  if (leader !== "bunny" && leader !== "lion") {
    throw new Error("RABBIT_CHARACTER: Choose bunny or lion for the companion scene.");
  }
  const alert = config.sprites.bunny?.animations?.alert;
  const width = alert?.widths[0];
  if (width === undefined) throw new Error("RABBIT_ALERT_CONFIG: Bunny alert animation needs a width.");
  const runWidth = config.sprites.lion?.animations?.run?.widths[0];
  if (runWidth === undefined) throw new Error("RABBIT_RUN_CONFIG: Lion run animation needs a width.");
  const [companion, left, right, runLeft, runRight] = await Promise.all([
    loadCharacterFrames(config, leader === "bunny" ? "lion" : "bunny"),
    loadSpriteFrames("bunny", "alert", width, "left"),
    loadSpriteFrames("bunny", "alert", width, "right"),
    loadSpriteFrames("lion", "run", runWidth, "left"),
    loadSpriteFrames("lion", "run", runWidth, "right"),
  ]);
  return { companion, alertLeft: left.frames, alertRight: right.frames,
    lionSprint: { left: runLeft.frames, right: runRight.frames } };
}

export const _test_hooks = { loadAdventureAssets };
