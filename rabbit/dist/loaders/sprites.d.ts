/**
 * Sprite loading and animation timer utilities.
 */
import type { Config, Settings, AudioConfigRef } from "../types.js";
/** Module interface for sprite frame exports */
export interface SpriteModule {
    readonly frames: readonly string[];
}
/** Type guard for checking if value is a record */
declare function isRecord(value: unknown): value is Record<string, unknown>;
/** Type guard for checking if value is a string array */
declare function isStringArray(value: unknown): value is string[];
/** Type guard for Settings */
declare function isSettings(value: unknown): value is Settings;
/** Validates that a module has the required frames property */
declare function validateSpriteModule(module: unknown, path: string): SpriteModule;
/** Validates optional audio config and returns typed result */
declare function validateOptionalAudio(value: unknown): AudioConfigRef | undefined;
/** Validates config structure */
declare function validateConfig(data: unknown): Config;
/** Animation timer interface */
export interface AnimationTimer {
    start: () => void;
    stop: () => void;
    isRunning: () => boolean;
}
export declare function createAnimationTimer(intervalMs: number, onTick: () => void): AnimationTimer;
/** Test hooks for internal functions - only exported for testing */
export declare const _test_hooks: {
    isRecord: typeof isRecord;
    isStringArray: typeof isStringArray;
    isSettings: typeof isSettings;
    validateSpriteModule: typeof validateSpriteModule;
    validateOptionalAudio: typeof validateOptionalAudio;
    validateConfig: typeof validateConfig;
};
export {};
//# sourceMappingURL=sprites.d.ts.map