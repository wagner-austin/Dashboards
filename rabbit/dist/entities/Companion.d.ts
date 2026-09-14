/** A companion follows in world units, with its own speed and animation clock. */
import type { BunnyFrames } from "./Bunny.js";
export interface CompanionState {
    readonly x: number;
    readonly z: number;
    readonly facingRight: boolean;
    readonly mode: "idle" | "walk" | "run" | "jump" | "hopAway" | "hopToward" | "turnAway" | "turnToward" | "settle";
    readonly clock: number;
    readonly jumpTime: number;
    readonly wasLeaderJumping: boolean;
}
export interface SprintFrames {
    readonly left: readonly string[];
    readonly right: readonly string[];
}
export interface CompanionInput {
    readonly deltaTime: number;
    readonly cameraDx: number;
    readonly cameraDz: number;
    readonly facingRight: boolean;
    readonly jumping: boolean;
}
export declare function createCompanion(): CompanionState;
/** Speed is bounded and stopping never overshoots, even after a long frame. */
export declare function stepCompanion(state: CompanionState, input: CompanionInput): CompanionState;
/** Fixed frame canvases preserve the jump's actual vertical motion. */
export declare function companionFrame(state: CompanionState, frames: BunnyFrames, sprint: SprintFrames): string[];
declare function transitionMode(state: CompanionState, requested: CompanionState["mode"]): CompanionState["mode"];
declare function selectSequence(state: CompanionState, frames: BunnyFrames, sprint: SprintFrames): readonly string[];
export declare const _test_hooks: {
    createCompanion: typeof createCompanion;
    stepCompanion: typeof stepCompanion;
    companionFrame: typeof companionFrame;
    transitionMode: typeof transitionMode;
    selectSequence: typeof selectSequence;
};
export {};
//# sourceMappingURL=Companion.d.ts.map