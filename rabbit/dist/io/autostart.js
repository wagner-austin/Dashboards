/**
 * Browser auto-start module.
 * Handles automatic initialization when loaded in browser.
 * Excluded from unit test coverage.
 */
import { init } from "../main.js";
// Vitest sets import.meta.env.MODE to 'test'
function isTestEnvironment() {
    const meta = import.meta;
    return meta.env?.MODE === "test";
}
if (!isTestEnvironment() && typeof document !== "undefined") {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            init().catch((error) => {
                console.error("Failed to initialize:", error);
            });
        });
    }
    else {
        init().catch((error) => {
            console.error("Failed to initialize:", error);
        });
    }
}
//# sourceMappingURL=autostart.js.map