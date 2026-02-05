/**
 * Bunny entity - state, animations, and frame selection.
 */
import { type AnimationTimer } from "../loaders/sprites.js";
export type BunnyAnimation = "walk" | "jump" | "idle" | "walk_to_idle" | "idle_to_walk";
export interface BunnyState {
    facingRight: boolean;
    currentAnimation: BunnyAnimation;
    bunnyFrameIdx: number;
    isJumping: boolean;
    jumpFrameIdx: number;
    isWalking: boolean;
    pendingJump: boolean;
    preJumpAnimation: BunnyAnimation | null;
}
export interface BunnyFrames {
    walkLeft: readonly string[];
    walkRight: readonly string[];
    jumpLeft: readonly string[];
    jumpRight: readonly string[];
    idleLeft: readonly string[];
    idleRight: readonly string[];
    walkToIdleLeft: readonly string[];
    walkToIdleRight: readonly string[];
}
export interface BunnyTimers {
    walk: AnimationTimer;
    idle: AnimationTimer;
    jump: AnimationTimer;
    transition: AnimationTimer;
}
export declare function createInitialBunnyState(): BunnyState;
export declare function createBunnyTimers(state: BunnyState, frames: BunnyFrames, intervals: {
    walk: number;
    idle: number;
    jump: number;
    transition: number;
}): BunnyTimers;
export declare function getBunnyFrame(state: BunnyState, frames: BunnyFrames): {
    lines: string[];
    frameIdx: number;
};
//# sourceMappingURL=Bunny.d.ts.map