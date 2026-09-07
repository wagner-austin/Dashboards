/**
 * Bundle entry point.
 *
 * This file is the line that starts the program, and nothing else: the
 * decision it delegates to lives in bootstrap.ts, which is tested. What
 * remains here cannot be unit tested by construction — a unit test that
 * imported this module would start the engine, which is exactly what the
 * environment guard below prevents. It is the one file in src/ excluded from
 * coverage, and vitest.config.ts names it individually with that reason.
 */
import { init } from "../main.js";
import { bootstrap } from "./bootstrap.js";
// Vitest sets import.meta.env.MODE to 'test'
function isTestEnvironment() {
    const meta = import.meta;
    return meta.env?.MODE === "test";
}
if (!isTestEnvironment() && typeof document !== "undefined") {
    bootstrap({
        readyState: () => document.readyState,
        onDomReady: (handler) => {
            document.addEventListener("DOMContentLoaded", handler);
        },
        start: init,
        onError: (error) => {
            console.error("Failed to initialize:", error);
        },
    });
}
//# sourceMappingURL=autostart.js.map