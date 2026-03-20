/**
 * Audio player using Web Audio API.
 * Fetches audio as ArrayBuffer, decodes to AudioBuffer, plays via BufferSourceNode.
 * Supports crossfade between tracks using GainNode ramping.
 */
import type { AudioTrack, AudioState, AudioContextLike, FetchFn } from "./types.js";
/** Audio player interface. */
export interface AudioPlayer {
    play(track: AudioTrack): void;
    pause(): void;
    resume(): void;
    setVolume(volume: number): void;
    getState(): AudioState;
}
/** Dependencies for audio player. */
export interface AudioPlayerDeps {
    context: AudioContextLike;
    fetchFn: FetchFn;
    masterVolume: number;
}
/**
 * Create audio player with Web Audio API.
 *
 * Args:
 *     deps: Audio player dependencies.
 *
 * Returns:
 *     AudioPlayer instance.
 */
export declare function createAudioPlayer(deps: AudioPlayerDeps): AudioPlayer;
/** Test hooks for internal functions. */
export declare const _test_hooks: {
    createAudioPlayer: typeof createAudioPlayer;
    FADE_DURATION: number;
};
//# sourceMappingURL=AudioPlayer.d.ts.map