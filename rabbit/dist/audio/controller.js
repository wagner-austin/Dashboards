/**
 * Audio controller - manages audio playback lifecycle and track switching.
 * Initializes AudioContext on first user interaction to satisfy browser autoplay policies.
 */
import { createAudioPlayer } from "./AudioPlayer.js";
import { getDefaultTrack } from "./TrackSelector.js";
/**
 * Get track at index from tracks array.
 *
 * Args:
 *     tracks: Array of audio tracks.
 *     index: Index to retrieve.
 *
 * Returns:
 *     Track at index or undefined if out of bounds.
 */
function getTrackAtIndex(tracks, index) {
    return tracks[index];
}
/** Type guard for KeyboardEvent. */
function isKeyboardEvent(e) {
    return "key" in e;
}
/**
 * Setup audio to start on first user interaction.
 * Creates AudioContext and resumes it if suspended, then plays the track.
 *
 * Args:
 *     context: Audio context.
 *     player: Audio player.
 *     track: Track to play.
 *     deps: Audio dependencies.
 *
 * Returns:
 *     Cleanup function to remove event listeners.
 */
export function setupAudioStart(context, player, track, deps) {
    const start = () => {
        if (context.state === "suspended") {
            context.resume().then(() => {
                player.play(track);
            }).catch(() => {
                // Resume failed
            });
        }
        else {
            player.play(track);
        }
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
 *
 * Args:
 *     audio: Audio system.
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
 *
 * Args:
 *     audio: Audio system.
 *     addListenerFn: Function to add event listener.
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
 * Initialize audio system if enabled in config.
 *
 * Args:
 *     audioConfig: Audio configuration from config.json.
 *     deps: Audio dependencies.
 *
 * Returns:
 *     Audio system or null if disabled.
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
    const context = deps.createContext();
    const player = createAudioPlayer({
        context,
        fetchFn: deps.fetchFn,
        masterVolume: audioConfig.masterVolume,
    });
    const cleanup = setupAudioStart(context, player, track, deps);
    return {
        context,
        player,
        tracks: audioConfig.tracks,
        currentIndex: 0,
        cleanup,
    };
}
/** Test hooks for internal functions. */
export const _test_hooks = {
    getTrackAtIndex,
    isKeyboardEvent,
    setupAudioStart,
    switchToNextTrack,
    setupTrackSwitcher,
    initializeAudio,
};
//# sourceMappingURL=controller.js.map