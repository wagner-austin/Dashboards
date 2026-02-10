/**
 * Validation functions for layer configuration.
 * Uses require_* pattern for strict TypedDict validation.
 */
import type { LayerType, LayerDefinition } from "../types.js";
import type { ValidatedLayer } from "./types.js";
/** Type guard for checking if value is a record */
declare function isRecord(value: unknown): value is Record<string, unknown>;
/** Type guard for string array */
declare function isStringArray(value: unknown): value is string[];
/** Type guard for number array */
declare function isNumberArray(value: unknown): value is number[];
/** Type guard for LayerType */
declare function isLayerType(value: unknown): value is LayerType;
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
    requireLayerDefinition: typeof requireLayerDefinition;
    toValidatedLayer: typeof toValidatedLayer;
    DEFAULT_LAYER: number;
};
export {};
//# sourceMappingURL=validation.d.ts.map