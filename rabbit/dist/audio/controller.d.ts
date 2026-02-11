/**
 * Audio controller - manages audio playback lifecycle and track switching.
 * Handles browser autoplay restrictions via user interaction triggers.
 */
import { type AudioPlayer } from "./AudioPlayer.js";
import type { AudioTrack, AudioConfig, AudioDependencies } from "./types.js";
export type { AudioDependencies };
/** Audio system state for track switching */
export interface AudioSystem {
    player: AudioPlayer;
    tracks: readonly AudioTrack[];
    currentIndex: number;
    cleanup: () => void;
}
/**
 * Get track at index from tracks array.
 * Returns undefined if index is out of bounds.
 */
declare function getTrackAtIndex(tracks: readonly AudioTrack[], index: number): AudioTrack | undefined;
/** Type guard for KeyboardEvent */
declare function isKeyboardEvent(e: Event): e is KeyboardEvent;
/**
 * Setup audio to start on first user interaction.
 * Required for iOS/Safari which blocks autoplay.
 */
export declare function setupAudioStart(player: AudioPlayer, track: AudioTrack, deps: AudioDependencies): () => void;
/**
 * Switch to next track with crossfade.
 * Cycles through available tracks.
 */
export declare function switchToNextTrack(audio: AudioSystem): void;
/**
 * Setup keyboard listener for track switching (N key).
 */
export declare function setupTrackSwitcher(audio: AudioSystem, addListenerFn: (type: string, handler: (e: Event) => void) => void): void;
/**
 * Initialize audio player if audio is enabled in config.
 * Returns the audio system with player and tracks, or null if disabled.
 */
export declare function initializeAudio(audioConfig: AudioConfig | undefined, deps: AudioDependencies): AudioSystem | null;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    getTrackAtIndex: typeof getTrackAtIndex;
    isKeyboardEvent: typeof isKeyboardEvent;
    setupAudioStart: typeof setupAudioStart;
    switchToNextTrack: typeof switchToNextTrack;
    setupTrackSwitcher: typeof setupTrackSwitcher;
    initializeAudio: typeof initializeAudio;
};
//# sourceMappingURL=controller.d.ts.map