/**
 * Sprite loading and animation timer utilities.
 */
import { validateAudioConfig } from "../audio/index.js";
import { validateAutorunConfig } from "../input/validation.js";
/** Type guard for checking if value is a record */
function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}
/** Type guard for checking if value is a string array */
function isStringArray(value) {
    if (!Array.isArray(value))
        return false;
    for (const item of value) {
        if (typeof item !== "string")
            return false;
    }
    return true;
}
/** Type guard for AnimationIntervals */
function isAnimationIntervals(value) {
    if (!isRecord(value))
        return false;
    return (typeof value.walk === "number" &&
        typeof value.idle === "number" &&
        typeof value.jump === "number" &&
        typeof value.transition === "number" &&
        typeof value.hop === "number");
}
/** Type guard for Settings */
function isSettings(value) {
    if (!isRecord(value))
        return false;
    return (typeof value.fps === "number" &&
        typeof value.scrollSpeed === "number" &&
        typeof value.depthSpeed === "number" &&
        isAnimationIntervals(value.animation));
}
/** Validates that a module has the required frames property */
function validateSpriteModule(module, path) {
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
function validateOptionalAudio(value) {
    if (value === undefined) {
        return undefined;
    }
    // Delegate to audio module's validation
    return validateAudioConfig(value);
}
/** Validates config structure */
function validateConfig(data) {
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
    const autoLayers = data.autoLayers;
    // An absent autorun block decodes to defaults, so the field is always present.
    const autorun = validateAutorunConfig(data.autorun);
    return {
        sprites: sprites,
        layers: layers,
        settings,
        autorun,
        ...(audio !== undefined ? { audio } : {}),
        ...(autoLayers !== undefined
            ? { autoLayers: autoLayers }
            : {}),
    };
}
export function createAnimationTimer(intervalMs, onTick) {
    let id = null;
    return {
        start() {
            if (id !== null)
                return;
            id = setInterval(onTick, intervalMs);
        },
        stop() {
            if (id !== null) {
                clearInterval(id);
                id = null;
            }
        },
        isRunning() {
            return id !== null;
        },
    };
}
/** Test hooks for internal functions - only exported for testing */
export const _test_hooks = {
    isRecord,
    isStringArray,
    isAnimationIntervals,
    isSettings,
    validateSpriteModule,
    validateOptionalAudio,
    validateConfig,
};
//# sourceMappingURL=sprites.js.map