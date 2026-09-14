/** Load the additional sequences required by the two-character scene. */
import type { Config } from "../types.js";
import type { AdventureAssets } from "../entities/Adventure.js";
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
export declare function loadAdventureAssets(config: Config, leader: string): Promise<AdventureAssets>;
export declare const _test_hooks: {
    loadAdventureAssets: typeof loadAdventureAssets;
};
//# sourceMappingURL=adventure-io.d.ts.map