/**
 * Validation functions for layer configuration.
 * Uses require_* pattern for strict TypedDict validation.
 */

import type { LayerType, LayerDefinition } from "../types.js";
import type { ValidatedLayer } from "./types.js";

/** Type guard for checking if value is a record */
function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Type guard for string array */
function isStringArray(value: unknown): value is string[] {
  if (!Array.isArray(value)) return false;
  for (const item of value) {
    if (typeof item !== "string") return false;
  }
  return true;
}

/** Type guard for number array */
function isNumberArray(value: unknown): value is number[] {
  if (!Array.isArray(value)) return false;
  for (const item of value) {
    if (typeof item !== "number") return false;
  }
  return true;
}

/** Type guard for LayerType */
function isLayerType(value: unknown): value is LayerType {
  return value === "static" || value === "tile" || value === "sprites";
}

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
function requireLayerDefinition(value: unknown, index: number): LayerDefinition {
  if (!isRecord(value)) {
    throw new Error(`layers[${String(index)}]: must be an object`);
  }

  const name = value.name;
  if (typeof name !== "string" || name.length === 0) {
    throw new Error(`layers[${String(index)}]: missing or invalid "name" field`);
  }

  const type = value.type;
  if (type !== undefined && !isLayerType(type)) {
    throw new Error(`layers[${String(index)}] "${name}": invalid "type" (must be static|tile|sprites)`);
  }

  const sprites = value.sprites;
  if (sprites !== undefined && !isStringArray(sprites)) {
    throw new Error(`layers[${String(index)}] "${name}": "sprites" must be string array`);
  }

  const positions = value.positions;
  if (positions !== undefined && !isNumberArray(positions)) {
    throw new Error(`layers[${String(index)}] "${name}": "positions" must be number array`);
  }

  const layer = value.layer;
  if (layer !== undefined && typeof layer !== "number") {
    throw new Error(`layers[${String(index)}] "${name}": "layer" must be a number`);
  }

  const tile = value.tile;
  if (tile !== undefined && typeof tile !== "boolean") {
    throw new Error(`layers[${String(index)}] "${name}": "tile" must be a boolean`);
  }

  // Build result with only defined properties (no undefined values)
  return {
    name,
    ...(type !== undefined ? { type } : {}),
    ...(sprites !== undefined ? { sprites } : {}),
    ...(positions !== undefined ? { positions } : {}),
    ...(layer !== undefined ? { layer } : {}),
    ...(tile !== undefined ? { tile } : {}),
  };
}

/** Default layer number when not specified */
const DEFAULT_LAYER = 10;

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
function toValidatedLayer(definition: LayerDefinition, zIndex: number): ValidatedLayer {
  return {
    name: definition.name,
    type: definition.type ?? "sprites",
    layer: definition.layer ?? DEFAULT_LAYER,
    spriteNames: definition.sprites ?? [],
    positions: definition.positions ?? [],
    zIndex,
    tile: definition.tile ?? false,
  };
}

/**
 * Validate entire layers array from config.
 * Ensures no duplicate names, valid structure.
 */
export function validateLayersConfig(layers: unknown): readonly ValidatedLayer[] {
  if (!Array.isArray(layers)) {
    throw new Error("layers: must be an array");
  }

  const validated: ValidatedLayer[] = [];
  const names = new Set<string>();

  for (let i = 0; i < layers.length; i++) {
    const def = requireLayerDefinition(layers[i], i);

    if (names.has(def.name)) {
      throw new Error(`layers[${String(i)}]: duplicate layer name "${def.name}"`);
    }
    names.add(def.name);

    validated.push(toValidatedLayer(def, i));
  }

  return validated;
}

/** Test hooks for internal functions */
export const _test_hooks = {
  isRecord,
  isStringArray,
  isNumberArray,
  isLayerType,
  requireLayerDefinition,
  toValidatedLayer,
  DEFAULT_LAYER,
};
