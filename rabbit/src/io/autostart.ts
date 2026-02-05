/**
 * Browser auto-start module.
 * Handles automatic initialization when loaded in browser.
 * Excluded from unit test coverage.
 */

import { init } from "../main.js";

// Vitest sets import.meta.env.MODE to 'test'
function isTestEnvironment(): boolean {
  const meta = import.meta as { env?: { MODE?: string } };
  return meta.env?.MODE === "test";
}

if (!isTestEnvironment() && typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      init().catch((error: unknown) => {
        console.error("Failed to initialize:", error);
      });
    });
  } else {
    init().catch((error: unknown) => {
      console.error("Failed to initialize:", error);
    });
  }
}
