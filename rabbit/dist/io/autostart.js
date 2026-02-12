/**
 * Browser auto-start module.
 * Handles automatic initialization when loaded in browser.
 * Excluded from unit test coverage.
 */
import { init } from "../main.js";
/** Debug log to screen overlay. */
function debug(msg) {
    if (typeof window !== "undefined") {
        const win = window;
        if (win.debugLog !== undefined) {
            win.debugLog(msg);
            return;
        }
    }
    console.log(msg);
}
// Vitest sets import.meta.env.MODE to 'test'
function isTestEnvironment() {
    const meta = import.meta;
    return meta.env?.MODE === "test";
}
if (!isTestEnvironment() && typeof document !== "undefined") {
    debug("[autostart] Module loaded");
    if (document.readyState === "loading") {
        debug("[autostart] Waiting for DOMContentLoaded");
        document.addEventListener("DOMContentLoaded", () => {
            debug("[autostart] DOMContentLoaded fired, calling init()");
            init().catch((error) => {
                debug(`[autostart] Init failed: ${String(error)}`);
                console.error("Failed to initialize:", error);
            });
        });
    }
    else {
        debug("[autostart] DOM ready, calling init()");
        init().catch((error) => {
            debug(`[autostart] Init failed: ${String(error)}`);
            console.error("Failed to initialize:", error);
        });
    }
}
//# sourceMappingURL=autostart.js.map