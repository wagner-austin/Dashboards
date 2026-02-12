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
 *     getAudio: Function returning audio system or null if not yet initialized.
 *     addListenerFn: Function to add event listener.
 */
export function setupTrackSwitcher(getAudio, addListenerFn) {
    const handleKey = (e) => {
        if (isKeyboardEvent(e) && (e.key === "n" || e.key === "N")) {
            const audio = getAudio();
            if (audio !== null) {
                switchToNextTrack(audio);
            }
        }
    };
    addListenerFn("keydown", handleKey);
}
/**
 * Initialize audio system if enabled in config.
 * AudioContext is created lazily on first user interaction to satisfy
 * Android Chrome's requirement that AudioContext be created from a user gesture.
 *
 * Args:
 *     audioConfig: Audio configuration from config.json.
 *     deps: Audio dependencies.
 *
 * Returns:
 *     Deferred audio system or null if disabled.
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
    let system = null;
    const start = () => {
        if (system !== null) {
            return;
        }
        const context = deps.createContext();
        const player = createAudioPlayer({
            context,
            fetchFn: deps.fetchFn,
            masterVolume: audioConfig.masterVolume,
        });
        system = {
            context,
            player,
            tracks: audioConfig.tracks,
            currentIndex: 0,
            cleanup: () => {
                deps.removeEventListenerFn("click", start);
                deps.removeEventListenerFn("touchstart", start);
                deps.removeEventListenerFn("touchend", start);
                deps.removeEventListenerFn("keydown", start);
            },
        };
        if (context.state === "suspended") {
            context.resume().then(() => {
                player.play(track);
            }).catch(() => {
                // Resume failed - try playing anyway
                player.play(track);
            });
        }
        else {
            player.play(track);
        }
        deps.removeEventListenerFn("click", start);
        deps.removeEventListenerFn("touchstart", start);
        deps.removeEventListenerFn("touchend", start);
        deps.removeEventListenerFn("keydown", start);
    };
    deps.addEventListenerFn("click", start);
    deps.addEventListenerFn("touchstart", start);
    deps.addEventListenerFn("touchend", start);
    deps.addEventListenerFn("keydown", start);
    return {
        tracks: audioConfig.tracks,
        currentIndex: 0,
        cleanup: () => {
            deps.removeEventListenerFn("click", start);
            deps.removeEventListenerFn("touchstart", start);
            deps.removeEventListenerFn("touchend", start);
            deps.removeEventListenerFn("keydown", start);
        },
        getSystem: () => system,
    };
}
/** Test hooks for internal functions. */
export const _test_hooks = {
    getTrackAtIndex,
    isKeyboardEvent,
    switchToNextTrack,
    setupTrackSwitcher,
    initializeAudio,
};
//# sourceMappingURL=controller.js.map