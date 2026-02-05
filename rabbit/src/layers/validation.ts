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

/** Type guard for LayerType */
function isLayerType(value: unknown): value is LayerType {
  return value === "static" || value === "tile" || value === "sprites";
}

/**
 * Require valid LayerDefinition from config.
 * Throws descriptive error if invalid.
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

  const parallax = value.parallax;
  if (parallax !== undefined && typeof parallax !== "number") {
    throw new Error(`layers[${String(index)}] "${name}": "parallax" must be a number`);
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
    ...(parallax !== undefined ? { parallax } : {}),
    ...(tile !== undefined ? { tile } : {}),
  };
}

/**
 * Convert LayerDefinition to ValidatedLayer with defaults applied.
 */
function toValidatedLayer(definition: LayerDefinition, zIndex: number): ValidatedLayer {
  return {
    name: definition.name,
    type: definition.type ?? "sprites",
    parallax: definition.parallax ?? 1.0,
    spriteNames: definition.sprites ?? [],
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
  isLayerType,
  requireLayerDefinition,
  toValidatedLayer,
};
