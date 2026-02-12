/**
 * Browser-specific I/O code.
 * This module contains code that requires browser APIs and is excluded from unit test coverage.
 * Testability is ensured through dependency injection in consuming modules.
 */
import type { AudioContextLike, AudioDependencies } from "../audio/types.js";
/**
 * Create browser AudioContext.
 *
 * Returns:
 *     AudioContext for Web Audio API.
 */
export declare function createBrowserAudioContext(): AudioContextLike;
/**
 * Create default audio dependencies for browser use.
 *
 * Returns:
 *     AudioDependencies with browser implementations.
 */
export declare function createDefaultAudioDependencies(): AudioDependencies;
//# sourceMappingURL=browser.d.ts.map