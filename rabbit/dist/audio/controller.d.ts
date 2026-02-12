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
 *     getAudio: Function returning audio system or null if not yet initialized.
 *     addListenerFn: Function to add event listener.
 */
export declare function setupTrackSwitcher(getAudio: () => AudioSystem | null, addListenerFn: (type: string, handler: (e: Event) => void) => void): void;
/** Deferred audio system created on first user interaction. */
export interface DeferredAudioSystem {
    tracks: readonly AudioTrack[];
    currentIndex: number;
    cleanup: () => void;
    getSystem: () => AudioSystem | null;
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
export declare function initializeAudio(audioConfig: AudioConfig | undefined, deps: AudioDependencies): DeferredAudioSystem | null;
/** Test hooks for internal functions. */
export declare const _test_hooks: {
    getTrackAtIndex: typeof getTrackAtIndex;
    isKeyboardEvent: typeof isKeyboardEvent;
    switchToNextTrack: typeof switchToNextTrack;
    setupTrackSwitcher: typeof setupTrackSwitcher;
    initializeAudio: typeof initializeAudio;
};
//# sourceMappingURL=controller.d.ts.map