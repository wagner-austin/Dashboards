/**
 * Core type definitions for the audio system.
 * Uses Web Audio API for reliable cross-browser playback.
 */
/** Time of day for conditional track selection. */
export type TimeOfDay = "day" | "night" | "dawn" | "dusk";
/** Tags for conditional track selection. */
export interface TrackTags {
    readonly time?: TimeOfDay;
    readonly location?: string;
}
/** Single audio track definition from config. */
export interface AudioTrack {
    readonly id: string;
    readonly path: string;
    readonly volume: number;
    readonly loop: boolean;
    readonly tags: TrackTags;
}
/** Audio configuration from config.json. */
export interface AudioConfig {
    readonly enabled: boolean;
    readonly masterVolume: number;
    readonly tracks: readonly AudioTrack[];
}
/** Runtime audio state snapshot. */
export interface AudioState {
    readonly currentTrackId: string | null;
    readonly isPlaying: boolean;
    readonly volume: number;
}
/** Create initial audio state. */
export declare function createAudioState(): AudioState;
/** Audio context wrapper for dependency injection. */
export interface AudioContextLike {
    readonly state: AudioContextState;
    resume(): Promise<void>;
    createBuffer(numberOfChannels: number, length: number, sampleRate: number): AudioBuffer;
    createBufferSource(): AudioBufferSourceNodeLike;
    createGain(): GainNodeLike;
    decodeAudioData(data: ArrayBuffer): Promise<AudioBuffer>;
    readonly destination: AudioNode;
}
/** AudioContext state values. */
export type AudioContextState = "suspended" | "running" | "closed";
/** Buffer source node wrapper. */
export interface AudioBufferSourceNodeLike {
    buffer: AudioBuffer | null;
    loop: boolean;
    connect(destination: AudioNode | GainNodeLike): void;
    start(when?: number): void;
    stop(when?: number): void;
    onended: (() => void) | null;
}
/** Gain node wrapper. */
export interface GainNodeLike {
    readonly gain: AudioParamLike;
    connect(destination: AudioNode): void;
}
/** Audio param wrapper. */
export interface AudioParamLike {
    value: number;
    linearRampToValueAtTime(value: number, endTime: number): void;
}
/** Fetch function signature. */
export type FetchFn = (url: string) => Promise<Response>;
/** Audio dependencies for dependency injection. */
export interface AudioDependencies {
    createContext: () => AudioContextLike;
    fetchFn: FetchFn;
    addEventListenerFn: (type: string, handler: () => void) => void;
    removeEventListenerFn: (type: string, handler: () => void) => void;
}
/** Test hooks for internal functions. */
export declare const _test_hooks: {
    createAudioState: typeof createAudioState;
};
//# sourceMappingURL=types.d.ts.map