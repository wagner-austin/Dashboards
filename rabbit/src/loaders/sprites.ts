/**
 * Sprite loading and animation timer utilities.
 */

import type { Config, Settings, AudioConfigRef } from "../types.js";
import { validateAudioConfig } from "../audio/index.js";

/** Module interface for sprite frame exports */
export interface SpriteModule {
  readonly frames: readonly string[];
}

/** Type guard for checking if value is a record */
function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Type guard for checking if value is a string array */
function isStringArray(value: unknown): value is string[] {
  if (!Array.isArray(value)) return false;
  for (const item of value) {
    if (typeof item !== "string") return false;
  }
  return true;
}

/** Type guard for Settings */
function isSettings(value: unknown): value is Settings {
  if (!isRecord(value)) return false;
  return (
    typeof value.fps === "number" &&
    typeof value.jumpSpeed === "number" &&
    typeof value.scrollSpeed === "number"
  );
}

/** Validates that a module has the required frames property */
function validateSpriteModule(module: unknown, path: string): SpriteModule {
  if (!isRecord(module)) {
    throw new Error(`Invalid sprite module at ${path}: not an object`);
  }
  const frames = module.frames;
  if (!isStringArray(frames)) {
    throw new Error(`Invalid sprite module at ${path}: frames must be string array`);
  }
  return { frames };
}

/** Validates optional audio config and returns typed result */
function validateOptionalAudio(value: unknown): AudioConfigRef | undefined {
  if (value === undefined) {
    return undefined;
  }
  // Delegate to audio module's validation
  return validateAudioConfig(value);
}

/** Validates config structure */
function validateConfig(data: unknown): Config {
  if (!isRecord(data)) {
    throw new Error("Invalid config: not an object");
  }
  const sprites = data.sprites;
  if (!isRecord(sprites)) {
    throw new Error("Invalid config: missing sprites object");
  }
  const layers = data.layers;
  if (!Array.isArray(layers)) {
    throw new Error("Invalid config: missing layers array");
  }
  const settings = data.settings;
  if (!isSettings(settings)) {
    throw new Error("Invalid config: invalid settings object");
  }
  const audio = validateOptionalAudio(data.audio);
  // After validation, we construct a properly typed object
  return {
    sprites: sprites as Config["sprites"],
    layers: layers as Config["layers"],
    settings,
    ...(audio !== undefined ? { audio } : {}),
  };
}


/** Animation timer interface */
export interface AnimationTimer {
  start: () => void;
  stop: () => void;
  isRunning: () => boolean;
}

export function createAnimationTimer(
  intervalMs: number,
  onTick: () => void
): AnimationTimer {
  let id: ReturnType<typeof setInterval> | null = null;

  return {
    start(): void {
      if (id !== null) return;
      id = setInterval(onTick, intervalMs);
    },
    stop(): void {
      if (id !== null) {
        clearInterval(id);
        id = null;
      }
    },
    isRunning(): boolean {
      return id !== null;
    },
  };
}

/** Test hooks for internal functions - only exported for testing */
export const _test_hooks = {
  isRecord,
  isStringArray,
  isSettings,
  validateSpriteModule,
  validateOptionalAudio,
  validateConfig,
};
