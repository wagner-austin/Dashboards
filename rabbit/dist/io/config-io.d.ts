/**
 * Fetching and decoding config.json.
 *
 * Separate from the sprite transport because it is the one asset that is not
 * a sprite module: it arrives as JSON over fetch and is validated by the
 * config decoder rather than the sprite-module guard.
 */
import type { Config } from "../types.js";
/**
 * Load and validate config.json.
 *
 * Returns:
 *     The decoded config.
 *
 * Raises:
 *     Error: If the document does not satisfy the config shape.
 */
export declare function loadConfig(): Promise<Config>;
//# sourceMappingURL=config-io.d.ts.map