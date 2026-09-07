/**
 * The order sprites load in, and when the controls unlock.
 *
 * Ordering is a policy, not a transport concern: the ground is instant, the
 * grass is cheap, the character unlocks input, and the trees stream in
 * smallest-first behind it. Keeping it in its own module means the order can
 * be read and changed without scrolling past every loader it calls.
 */
import type { Config } from "../types.js";
import type { BunnyFrames } from "../entities/Bunny.js";
import type { MutableSpriteRegistry, ProgressCallback } from "../loaders/progressive.js";
/**
 * Callback invoked when the character's frames finish loading.
 */
export type BunnyLoadedCallback = (frames: BunnyFrames) => void;
/**
 * Run progressive loading sequence.
 *
 * Loads sprites in order: ground, grass, character, trees (smallest to
 * largest). Calls onProgress for each loaded sprite to enable UI updates.
 * Calls onBunnyLoaded immediately when the character's frames are ready,
 * before trees, so movement is available while the forest is still arriving.
 *
 * Args:
 *     config: Application config.
 *     character: Character sprite name, resolved by resolveCharacterName.
 *     registry: Mutable sprite registry to populate.
 *     onProgress: Progress callback for each loaded sprite.
 *     onBunnyLoaded: Callback when character frames are ready (before trees).
 */
export declare function runProgressiveLoad(config: Config, character: string, registry: MutableSpriteRegistry, onProgress: ProgressCallback, onBunnyLoaded: BunnyLoadedCallback): Promise<void>;
//# sourceMappingURL=progressive-io.d.ts.map