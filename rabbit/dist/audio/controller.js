/**
 * Audio controller - manages audio playback lifecycle and track switching.
 * Handles browser autoplay restrictions via user interaction triggers.
 */
import { createAudioPlayer } from "./AudioPlayer.js";
import { getDefaultTrack } from "./TrackSelector.js";
/**
 * Get track at index from tracks array.
 * Returns undefined if index is out of bounds.
 */
function getTrackAtIndex(tracks, index) {
    return tracks[index];
}
/** Type guard for KeyboardEvent */
function isKeyboardEvent(e) {
    return "key" in e;
}
/**
 * Setup audio to start on first user interaction.
 * Required for iOS/Safari which blocks autoplay.
 */
export function setupAudioStart(player, track, deps) {
    const start = () => {
        player.play(track);
        deps.removeEventListenerFn("click", start);
        deps.removeEventListenerFn("touchstart", start);
        deps.removeEventListenerFn("keydown", start);
    };
    deps.addEventListenerFn("click", start);
    deps.addEventListenerFn("touchstart", start);
    deps.addEventListenerFn("keydown", start);
    return start;
}
/**
 * Switch to next track with crossfade.
 * Cycles through available tracks.
 */
export function switchToNextTrack(audio) {
    const trackCount = audio.tracks.length;
    if (trackCount <= 1) {
        return;
    }
    const nextIndex = (audio.currentIndex + 1) % trackCount;
    const nextTrack = getTrackAtIndex(audio.tracks, nextIndex);
    if (nextTrack === undefined) {
        return;
    }
    audio.currentIndex = nextIndex;
    audio.player.play(nextTrack);
}
/**
 * Setup keyboard listener for track switching (N key).
 */
export function setupTrackSwitcher(audio, addListenerFn) {
    const handleKey = (e) => {
        if (isKeyboardEvent(e) && (e.key === "n" || e.key === "N")) {
            switchToNextTrack(audio);
        }
    };
    addListenerFn("keydown", handleKey);
}
/**
 * Initialize audio player if audio is enabled in config.
 * Returns the audio system with player and tracks, or null if disabled.
 */
export function initializeAudio(audioConfig, deps) {
    if (audioConfig === undefined) {
        return null;
    }
    if (!audioConfig.enabled) {
        return null;
    }
    const track = getDefaultTrack(audioConfig.tracks);
    if (track === null) {
        return null;
    }
    const player = createAudioPlayer({
        createElement: deps.createElementFn,
        masterVolume: audioConfig.masterVolume,
    });
    const cleanup = setupAudioStart(player, track, deps);
    return {
        player,
        tracks: audioConfig.tracks,
        currentIndex: 0,
        cleanup,
    };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    getTrackAtIndex,
    isKeyboardEvent,
    setupAudioStart,
    switchToNextTrack,
    setupTrackSwitcher,
    initializeAudio,
};
//# sourceMappingURL=controller.js.map