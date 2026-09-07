/**
 * Fetching and decoding config.json.
 *
 * Separate from the sprite transport because it is the one asset that is not
 * a sprite module: it arrives as JSON over fetch and is validated by the
 * config decoder rather than the sprite-module guard.
 */

import type { Config } from "../types.js";
import { _test_hooks as spritesHooks } from "../loaders/sprites.js";
import { assetUrl, _test_hooks as transportHooks } from "./transport.js";

/**
 * Load and validate config.json.
 *
 * Returns:
 *     The decoded config.
 *
 * Raises:
 *     Error: If the document does not satisfy the config shape.
 */
export async function loadConfig(): Promise<Config> {
  const { validateConfig } = spritesHooks;
  const response = await transportHooks.fetchFn(assetUrl("config.json"));
  const data: unknown = await response.json();
  return validateConfig(data);
}
