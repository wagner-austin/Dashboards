/**
 * I/O module - browser and network operations.
 *
 * Four concerns, one file each: transport.ts owns the two calls that leave the
 * process, config-io.ts decodes config.json, character-io.ts assembles one
 * character's frames, scene-io.ts loads the scenery, and progressive-io.ts
 * owns the order they arrive in.
 */

export {
  createBrowserAudioContext,
  createDefaultAudioDependencies,
} from "./browser.js";

export {
  createDocumentKeyboardSource,
  createDocumentTouchSource,
} from "./events.js";

export { loadSpriteFrames, loadStaticSpriteFrames } from "./transport.js";
export type { SpriteModule } from "./transport.js";

export { loadConfig } from "./config-io.js";

export { loadCharacterFrames } from "./character-io.js";

export {
  loadTreeSizes,
  loadLayerSprites,
  loadGrassSprites,
  loadTreeSpritesProgressive,
} from "./scene-io.js";

export { runProgressiveLoad } from "./progressive-io.js";
export type { BunnyLoadedCallback } from "./progressive-io.js";
