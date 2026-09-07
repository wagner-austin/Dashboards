/**
 * Loading the scenery: trees, grass, and whatever else a layer names.
 *
 * Distinct from character-io.ts because scenery is loaded by width across
 * many sprites and reported progressively, while a character is loaded once
 * as a fixed set of animations. They share only the transport underneath.
 */
import type { Config } from "../types.js";
import type { TreeSize } from "../entities/Tree.js";
import type { ValidatedLayer } from "../layers/types.js";
import type { SpriteRegistry } from "../loaders/layers.js";
import type { MutableSpriteRegistry, ProgressCallback } from "../loaders/progressive.js";
/**
 * Load all tree size variations from config.
 *
 * Reads tree sprite widths from config and loads each size.
 * Returns sizes sorted smallest to largest.
 *
 * Args:
 *     config: Application config with sprite definitions.
 *
 * Returns:
 *     Array of TreeSize sorted by width ascending.
 */
export declare function loadTreeSizes(config: Config): Promise<TreeSize[]>;
/**
 * Load all sprites referenced by layers.
 *
 * Args:
 *     config: Application config.
 *     layers: Validated layers naming the sprites to load.
 *
 * Returns:
 *     A registry holding each named sprite at every width it declares.
 */
export declare function loadLayerSprites(config: Config, layers: readonly ValidatedLayer[]): Promise<SpriteRegistry>;
/**
 * Load grass sprites into mutable registry.
 *
 * Args:
 *     config: Application config.
 *     registry: Mutable sprite registry.
 *     onProgress: Progress callback.
 */
export declare function loadGrassSprites(config: Config, registry: MutableSpriteRegistry, onProgress: ProgressCallback): Promise<void>;
/**
 * Load tree sprites progressively from smallest to largest.
 *
 * Loads trees interleaved across tree types (tree1, tree2, etc.)
 * so that the smallest trees from all types load first.
 *
 * Args:
 *     config: Application config.
 *     registry: Mutable sprite registry.
 *     onProgress: Progress callback.
 */
export declare function loadTreeSpritesProgressive(config: Config, registry: MutableSpriteRegistry, onProgress: ProgressCallback): Promise<void>;
//# sourceMappingURL=scene-io.d.ts.map