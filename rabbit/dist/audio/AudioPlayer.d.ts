/**
 * Audio player with dependency injection for testability.
 * Uses HTMLAudioElement for cross-browser compatibility.
 * Supports fade-in on start and crossfade between tracks.
 */
import type { AudioTrack, AudioState, AudioElementLike } from "./types.js";
export type { AudioElementLike };
/** Audio player interface */
export interface AudioPlayer {
    play(track: AudioTrack): void;
    pause(): void;
    resume(): void;
    setVolume(volume: number): void;
    getState(): AudioState;
}
/** Dependencies for audio player */
export interface AudioPlayerDeps {
    createElement: () => AudioElementLike;
    masterVolume: number;
}
/**
 * Create audio player with injected dependencies.
 * Allows testing without actual Audio elements.
 */
export declare function createAudioPlayer(deps: AudioPlayerDeps): AudioPlayer;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createAudioPlayer: typeof createAudioPlayer;
};
//# sourceMappingURL=AudioPlayer.d.ts.map