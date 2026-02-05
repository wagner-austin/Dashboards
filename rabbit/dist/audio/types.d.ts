/**
 * Core type definitions for the audio system.
 * Supports ambient background music with modular track selection.
 */
/** Time of day for conditional track selection */
export type TimeOfDay = "day" | "night" | "dawn" | "dusk";
/** Tags for conditional track selection (future: time/location) */
export interface TrackTags {
    readonly time?: TimeOfDay;
    readonly location?: string;
}
/** Single audio track definition */
export interface AudioTrack {
    readonly id: string;
    readonly path: string;
    readonly volume: number;
    readonly loop: boolean;
    readonly tags: TrackTags;
}
/** Audio configuration from config.json */
export interface AudioConfig {
    readonly enabled: boolean;
    readonly masterVolume: number;
    readonly tracks: readonly AudioTrack[];
}
/** Runtime audio state (immutable snapshot) */
export interface AudioState {
    readonly currentTrackId: string | null;
    readonly isPlaying: boolean;
    readonly volume: number;
}
/** Create initial audio state */
export declare function createAudioState(): AudioState;
/** Audio element interface for dependency injection */
export interface AudioElementLike {
    src: string;
    volume: number;
    loop: boolean;
    play(): Promise<void>;
    pause(): void;
}
/** Audio dependencies for dependency injection */
export interface AudioDependencies {
    createElementFn: () => AudioElementLike;
    addEventListenerFn: (type: string, handler: () => void) => void;
    removeEventListenerFn: (type: string, handler: () => void) => void;
}
/** Test hooks for internal functions */
export declare const _test_hooks: {
    createAudioState: typeof createAudioState;
};
//# sourceMappingURL=types.d.ts.map