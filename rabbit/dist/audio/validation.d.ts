/**
 * Validation functions for audio configuration.
 * Uses require_* pattern for strict TypedDict validation.
 */
import type { AudioTrack, AudioConfig, TrackTags, TimeOfDay } from "./types.js";
/** Type guard for checking if value is a record */
declare function isRecord(value: unknown): value is Record<string, unknown>;
/** Type guard for TimeOfDay */
declare function isTimeOfDay(value: unknown): value is TimeOfDay;
/** Type guard for TrackTags */
declare function isTrackTags(value: unknown): value is TrackTags;
/**
 * Require valid AudioTrack from config.
 * Throws descriptive error if invalid.
 */
declare function requireAudioTrack(value: unknown, index: number): AudioTrack;
/**
 * Validate entire audio configuration from config.json.
 * Throws descriptive error if invalid.
 */
export declare function validateAudioConfig(config: unknown): AudioConfig;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    isRecord: typeof isRecord;
    isTimeOfDay: typeof isTimeOfDay;
    isTrackTags: typeof isTrackTags;
    requireAudioTrack: typeof requireAudioTrack;
};
export {};
//# sourceMappingURL=validation.d.ts.map