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
/** Type guard for LayerType */
declare function isLayerType(value: unknown): value is LayerType;
/**
 * Require valid LayerDefinition from config.
 * Throws descriptive error if invalid.
 */
declare function requireLayerDefinition(value: unknown, index: number): LayerDefinition;
/**
 * Convert LayerDefinition to ValidatedLayer with defaults applied.
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
    isLayerType: typeof isLayerType;
    requireLayerDefinition: typeof requireLayerDefinition;
    toValidatedLayer: typeof toValidatedLayer;
};
export {};
//# sourceMappingURL=validation.d.ts.map