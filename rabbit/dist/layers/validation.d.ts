/**
 * Validation functions for layer configuration.
 * Uses require_* pattern for strict TypedDict validation.
 */
import type { LayerType, LayerDefinition, AutoLayersConfig, LayerBehavior, LayerBehaviorPreset } from "../types.js";
import type { ValidatedLayer } from "./types.js";
/**
 * Seeded random number generator for consistent positions.
 * Uses simple LCG algorithm.
 */
declare function createSeededRandom(seed: number): () => number;
/**
 * Generate layer definitions automatically from config.
 *
 * Creates layers spread across the depth range with alternating sprites
 * and pseudo-random X positions (seeded for consistency).
 *
 * Args:
 *     config: Auto-layers configuration.
 *
 * Returns:
 *     Array of LayerDefinition to be validated.
 */
/**
 * Get sprite name at cycled index.
 *
 * Wraps index to stay within sprites array bounds using modulo.
 * Requires non-empty sprites array.
 *
 * Args:
 *     sprites: Non-empty sprite name array.
 *     index: Index that may exceed array length.
 *
 * Returns:
 *     Sprite name at wrapped index.
 *
 * Raises:
 *     Error: If sprites array is empty.
 */
declare function getSpriteAtIndex(sprites: readonly string[], index: number): string;
export declare function generateAutoLayers(config: AutoLayersConfig): LayerDefinition[];
/** Type guard for checking if value is a record */
declare function isRecord(value: unknown): value is Record<string, unknown>;
/** Type guard for string array */
declare function isStringArray(value: unknown): value is string[];
/** Type guard for number array */
declare function isNumberArray(value: unknown): value is number[];
/** Type guard for LayerType */
declare function isLayerType(value: unknown): value is LayerType;
/** Type guard for LayerBehaviorPreset */
declare function isBehaviorPreset(value: unknown): value is LayerBehaviorPreset;
/**
 * Infer layer behavior from layer definition.
 *
 * Uses explicit behavior if provided, otherwise infers from layer properties:
 * - type "static" → static behavior
 * - tile: true → foreground behavior
 * - has positions → midground behavior (scrolling objects)
 * - default → midground behavior
 *
 * Args:
 *     def: Layer definition with optional behavior.
 *
 * Returns:
 *     LayerBehavior for the layer.
 */
declare function inferBehavior(def: LayerDefinition): LayerBehavior;
/**
 * Require valid AutoLayersConfig from unknown input.
 *
 * Validates all fields and throws descriptive errors for invalid values.
 *
 * Args:
 *     value: Raw value to validate.
 *
 * Returns:
 *     Validated AutoLayersConfig.
 *
 * Raises:
 *     Error: If value is not a valid AutoLayersConfig.
 */
export declare function requireAutoLayersConfig(value: unknown): AutoLayersConfig;
/**
 * Require valid LayerDefinition from config.
 *
 * Validates all fields and throws descriptive errors for invalid values.
 *
 * Args:
 *     value: Raw value from config to validate.
 *     index: Index in layers array for error messages.
 *
 * Returns:
 *     Validated LayerDefinition.
 *
 * Raises:
 *     Error: If value is not a valid LayerDefinition.
 */
declare function requireLayerDefinition(value: unknown, index: number): LayerDefinition;
/**
 * Convert LayerDefinition to ValidatedLayer with defaults applied.
 *
 * Args:
 *     definition: Parsed layer definition from config.
 *     zIndex: Render order index.
 *
 * Returns:
 *     ValidatedLayer with all required fields populated.
 */
declare function toValidatedLayer(definition: LayerDefinition, zIndex: number): ValidatedLayer;
/**
 * Process layers config with optional auto-generation.
 *
 * If autoLayers config is provided, generates layers and prepends them
 * to any manually defined layers. All layers are then validated.
 *
 * Args:
 *     layers: Manual layer definitions array.
 *     autoLayers: Optional auto-layer generation config.
 *
 * Returns:
 *     Validated layers sorted by layer number (back to front).
 */
export declare function processLayersConfig(layers: unknown, autoLayers?: unknown): readonly ValidatedLayer[];
/**
 * Validate entire layers array from config.
 * Ensures no duplicate names, valid structure.
 */
export declare function validateLayersConfig(layers: unknown): readonly ValidatedLayer[];
/** Test hooks for internal functions */
export declare const _test_hooks: {
    isRecord: typeof isRecord;
    isStringArray: typeof isStringArray;
    isNumberArray: typeof isNumberArray;
    isLayerType: typeof isLayerType;
    isBehaviorPreset: typeof isBehaviorPreset;
    inferBehavior: typeof inferBehavior;
    requireLayerDefinition: typeof requireLayerDefinition;
    requireAutoLayersConfig: typeof requireAutoLayersConfig;
    toValidatedLayer: typeof toValidatedLayer;
    createSeededRandom: typeof createSeededRandom;
    getSpriteAtIndex: typeof getSpriteAtIndex;
    generateAutoLayers: typeof generateAutoLayers;
    DEFAULT_LAYER: number;
};
export {};
//# sourceMappingURL=validation.d.ts.map