/**
 * Track selection functions for ambient audio.
 * Supports selection by time of day, location, or default fallback.
 */
import type { AudioTrack, TimeOfDay } from "./types.js";
/**
 * Select first track matching time of day.
 * Returns null if no matching track found.
 */
export declare function selectTrackByTime(tracks: readonly AudioTrack[], time: TimeOfDay): AudioTrack | null;
/**
 * Select first track matching location.
 * Returns null if no matching track found.
 */
export declare function selectTrackByLocation(tracks: readonly AudioTrack[], location: string): AudioTrack | null;
/**
 * Get first track as default.
 * Returns null if tracks array is empty.
 */
export declare function getDefaultTrack(tracks: readonly AudioTrack[]): AudioTrack | null;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    selectTrackByTime: typeof selectTrackByTime;
    selectTrackByLocation: typeof selectTrackByLocation;
    getDefaultTrack: typeof getDefaultTrack;
};
//# sourceMappingURL=TrackSelector.d.ts.map