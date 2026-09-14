/** Companion movement and attentive idle poses, independent of browser I/O. */
import { type CompanionState, type SprintFrames } from "./Companion.js";
import type { BunnyFrames, BunnyState } from "./Bunny.js";
import type { Camera } from "../world/Projection.js";
export interface AdventureAssets {
    readonly lionSprint: SprintFrames;
    readonly companion: BunnyFrames;
    readonly alertLeft: readonly string[];
    readonly alertRight: readonly string[];
}
export interface AdventureVisual {
    readonly companionSprint: SprintFrames;
    readonly companion: CompanionState;
    readonly assets: AdventureAssets;
    readonly alert: readonly string[] | null;
    readonly companionColor: string;
    readonly status: string;
}
export interface AdventureSystem {
    readonly update: (dt: number, camera: Camera, bunny: BunnyState, sprinting: boolean) => AdventureVisual;
}
/**
 * Create an independently clocked companion and idle-pose service.
 *
 * Args:
 *   assets: Validated animation sequences, already loaded.
 *   leader: Selected character name.
 *   initialCamera: Starting camera used to measure real displacement.
 *   depthRange: Period of the world's depth wrapping.
 * Returns:
 *   A focused service producing immutable render snapshots.
 */
export declare function createAdventure(assets: AdventureAssets, leader: string, initialCamera: Camera, depthRange: number): AdventureSystem;
export declare const _test_hooks: {
    createAdventure: typeof createAdventure;
};
//# sourceMappingURL=Adventure.d.ts.map