/**
 * Audio controller - manages audio playback lifecycle and track switching.
 * Initializes AudioContext on first user interaction to satisfy browser autoplay policies.
 */
import { type AudioPlayer } from "./AudioPlayer.js";
import type { AudioTrack, AudioConfig, AudioDependencies, AudioContextLike } from "./types.js";
export type { AudioDependencies };
/** Audio system state for track switching. */
export interface AudioSystem {
    context: AudioContextLike;
    player: AudioPlayer;
    tracks: readonly AudioTrack[];
    currentIndex: number;
    cleanup: () => void;
}
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
declare function getTrackAtIndex(tracks: readonly AudioTrack[], index: number): AudioTrack | undefined;
/** Type guard for KeyboardEvent. */
declare function isKeyboardEvent(e: Event): e is KeyboardEvent;
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
export declare function setupAudioStart(context: AudioContextLike, player: AudioPlayer, track: AudioTrack, deps: AudioDependencies): () => void;
/**
 * Switch to next track with crossfade.
 *
 * Args:
 *     audio: Audio system.
 */
export declare function switchToNextTrack(audio: AudioSystem): void;
/**
 * Setup keyboard listener for track switching (N key).
 *
 * Args:
 *     audio: Audio system.
 *     addListenerFn: Function to add event listener.
 */
export declare function setupTrackSwitcher(audio: AudioSystem, addListenerFn: (type: string, handler: (e: Event) => void) => void): void;
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
export declare function initializeAudio(audioConfig: AudioConfig | undefined, deps: AudioDependencies): AudioSystem | null;
/** Test hooks for internal functions. */
export declare const _test_hooks: {
    getTrackAtIndex: typeof getTrackAtIndex;
    isKeyboardEvent: typeof isKeyboardEvent;
    setupAudioStart: typeof setupAudioStart;
    switchToNextTrack: typeof switchToNextTrack;
    setupTrackSwitcher: typeof setupTrackSwitcher;
    initializeAudio: typeof initializeAudio;
};
//# sourceMappingURL=controller.d.ts.map