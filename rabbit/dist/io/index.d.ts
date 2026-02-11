/**
 * I/O module - browser and network operations.
 * This module is excluded from unit test coverage.
 * All functions here are testable through dependency injection in consuming modules.
 */
export { createBrowserAudioElement, createDefaultAudioDependencies, } from "./browser.js";
export { loadConfig, loadSpriteFrames, loadStaticSpriteFrames, loadBunnyFrames, loadTreeSizes, loadLayerSprites, loadGrassSprites, loadTreeSpritesProgressive, runProgressiveLoad, } from "./sprites.js";
export type { SpriteModule, BunnyLoadedCallback } from "./sprites.js";
//# sourceMappingURL=index.d.ts.map