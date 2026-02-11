/**
 * Track selection functions for ambient audio.
 * Supports selection by time of day, location, or default fallback.
 */
/**
 * Select first track matching time of day.
 * Returns null if no matching track found.
 */
export function selectTrackByTime(tracks, time) {
    for (const track of tracks) {
        if (track.tags.time === time) {
            return track;
        }
    }
    return null;
}
/**
 * Select first track matching location.
 * Returns null if no matching track found.
 */
export function selectTrackByLocation(tracks, location) {
    for (const track of tracks) {
        if (track.tags.location === location) {
            return track;
        }
    }
    return null;
}
/**
 * Get first track as default.
 * Returns null if tracks array is empty.
 */
export function getDefaultTrack(tracks) {
    const first = tracks[0];
    if (first === undefined) {
        return null;
    }
    return first;
}
/** Test hooks for internal functions */
export const _test_hooks = {
    selectTrackByTime,
    selectTrackByLocation,
    getDefaultTrack,
};
//# sourceMappingURL=TrackSelector.js.map