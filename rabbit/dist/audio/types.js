/**
 * Core type definitions for the audio system.
 * Uses Web Audio API for reliable cross-browser playback.
 */
/** Create initial audio state. */
export function createAudioState() {
    return {
        currentTrackId: null,
        isPlaying: false,
        volume: 1.0,
    };
}
/** Test hooks for internal functions. */
export const _test_hooks = {
    createAudioState,
};
//# sourceMappingURL=types.js.map