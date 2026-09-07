/**
 * The order sprites load in, and when the controls unlock.
 *
 * Ordering is a policy, not a transport concern: the ground is instant, the
 * grass is cheap, the character unlocks input, and the trees stream in
 * smallest-first behind it. Keeping it in its own module means the order can
 * be read and changed without scrolling past every loader it calls.
 */
import { loadCharacterFrames } from "./character-io.js";
import { loadGrassSprites, loadTreeSpritesProgressive } from "./scene-io.js";
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
export async function runProgressiveLoad(config, character, registry, onProgress, onBunnyLoaded) {
    // Phase 1: Ground (instant - notify only)
    onProgress({ phase: "ground", current: 1, total: 1, spriteName: "ground", width: 0 });
    // Phase 2: Grass sprites
    await loadGrassSprites(config, registry, onProgress);
    // Phase 3: Character frames - notify immediately when ready
    onProgress({ phase: "bunny", current: 1, total: 1, spriteName: character, width: 0 });
    onBunnyLoaded(await loadCharacterFrames(config, character));
    // Phase 4: Trees (smallest to largest)
    await loadTreeSpritesProgressive(config, registry, onProgress);
}
//# sourceMappingURL=progressive-io.js.map