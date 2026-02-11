/**
 * Validation functions for layer configuration.
 * Uses require_* pattern for strict TypedDict validation.
 */

import type {
  LayerType,
  LayerDefinition,
  AutoLayersConfig,
  LayerBehavior,
  LayerBehaviorPreset,
} from "../types.js";
import { LAYER_BEHAVIORS } from "../types.js";
import type { ValidatedLayer } from "./types.js";
import { WORLD_WIDTH } from "../world/Projection.js";

/**
 * Seeded random number generator for consistent positions.
 * Uses simple LCG algorithm.
 */
function createSeededRandom(seed: number): () => number {
  let state = seed;
  return (): number => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

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
function getSpriteAtIndex(sprites: readonly string[], index: number): string {
  if (sprites.length === 0) {
    throw new Error("autoLayers: sprites array is empty");
  }
  const wrapped = index % sprites.length;
  const spriteName = sprites[wrapped];
  if (spriteName === undefined) {
    throw new Error(`autoLayers: sprite index ${String(wrapped)} out of bounds`);
  }
  return spriteName;
}

export function generateAutoLayers(config: AutoLayersConfig): LayerDefinition[] {
  const layers: LayerDefinition[] = [];
  const random = createSeededRandom(config.seed ?? 12345);

  const layerCount = config.maxLayer - config.minLayer + 1;
  const sprites = config.sprites;
  const treesPerLayer = config.treesPerLayer ?? 2;

  for (let i = 0; i < layerCount; i++) {
    const layerNum = config.minLayer + i;
    const spriteName = getSpriteAtIndex(sprites, i);

    // Generate random positions for this layer
    const positions: number[] = [];
    for (let t = 0; t < treesPerLayer; t++) {
      // Spread positions across world width with some randomness
      const baseX = (t / treesPerLayer) * WORLD_WIDTH - WORLD_WIDTH / 2;
      const offset = (random() - 0.5) * 200;
      positions.push(Math.round(baseX + offset));
    }

    layers.push({
      name: `auto-trees-${String(layerNum)}`,
      sprites: [spriteName],
      layer: layerNum,
      positions,
    });
  }

  return layers;
}

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

/** Type guard for LayerBehaviorPreset */
function isBehaviorPreset(value: unknown): value is LayerBehaviorPreset {
  return (
    value === "static" ||
    value === "background" ||
    value === "midground" ||
    value === "foreground"
  );
}

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
function inferBehavior(def: LayerDefinition): LayerBehavior {
  if (def.behavior !== undefined) {
    return LAYER_BEHAVIORS[def.behavior];
  }

  if (def.type === "static") {
    return LAYER_BEHAVIORS.static;
  }

  if (def.tile === true) {
    return LAYER_BEHAVIORS.foreground;
  }

  return LAYER_BEHAVIORS.midground;
}

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
export function requireAutoLayersConfig(value: unknown): AutoLayersConfig {
  if (!isRecord(value)) {
    throw new Error("autoLayers: must be an object");
  }

  const sprites = value.sprites;
  if (!isStringArray(sprites) || sprites.length === 0) {
    throw new Error("autoLayers.sprites: must be non-empty string array");
  }

  const minLayer = value.minLayer;
  if (typeof minLayer !== "number" || !Number.isInteger(minLayer)) {
    throw new Error("autoLayers.minLayer: must be an integer");
  }

  const maxLayer = value.maxLayer;
  if (typeof maxLayer !== "number" || !Number.isInteger(maxLayer)) {
    throw new Error("autoLayers.maxLayer: must be an integer");
  }

  if (minLayer > maxLayer) {
    throw new Error("autoLayers: minLayer must be <= maxLayer");
  }

  const treesPerLayer = value.treesPerLayer;
  if (treesPerLayer !== undefined) {
    if (typeof treesPerLayer !== "number" || !Number.isInteger(treesPerLayer) || treesPerLayer < 1) {
      throw new Error("autoLayers.treesPerLayer: must be a positive integer");
    }
  }

  const seed = value.seed;
  if (seed !== undefined) {
    if (typeof seed !== "number" || !Number.isInteger(seed)) {
      throw new Error("autoLayers.seed: must be an integer");
    }
  }

  return {
    sprites,
    minLayer,
    maxLayer,
    ...(treesPerLayer !== undefined ? { treesPerLayer } : {}),
    ...(seed !== undefined ? { seed } : {}),
  };
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

  const behavior = value.behavior;
  if (behavior !== undefined && !isBehaviorPreset(behavior)) {
    throw new Error(
      `layers[${String(index)}] "${name}": "behavior" must be static|background|midground|foreground`
    );
  }

  // Build result with only defined properties (no undefined values)
  return {
    name,
    ...(type !== undefined ? { type } : {}),
    ...(sprites !== undefined ? { sprites } : {}),
    ...(positions !== undefined ? { positions } : {}),
    ...(layer !== undefined ? { layer } : {}),
    ...(tile !== undefined ? { tile } : {}),
    ...(behavior !== undefined ? { behavior } : {}),
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
    behavior: inferBehavior(definition),
  };
}

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
export function processLayersConfig(
  layers: unknown,
  autoLayers?: unknown
): readonly ValidatedLayer[] {
  const allLayers: unknown[] = [];

  // Generate auto layers if config provided
  if (autoLayers !== undefined) {
    const autoConfig = requireAutoLayersConfig(autoLayers);
    const generated = generateAutoLayers(autoConfig);
    allLayers.push(...generated);
  }

  // Add manual layers
  if (Array.isArray(layers)) {
    const manualLayers: readonly unknown[] = layers;
    for (const layer of manualLayers) {
      allLayers.push(layer);
    }
  }

  // Validate combined layers
  const validated = validateLayersConfig(allLayers);

  // Sort by layer number (highest first = back to front)
  return [...validated].sort((a, b) => b.layer - a.layer);
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
  isBehaviorPreset,
  inferBehavior,
  requireLayerDefinition,
  requireAutoLayersConfig,
  toValidatedLayer,
  createSeededRandom,
  getSpriteAtIndex,
  generateAutoLayers,
  DEFAULT_LAYER,
};
