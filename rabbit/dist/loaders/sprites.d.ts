/**
 * Sprite loading and animation timer utilities.
 */
import type { Config, FrameSet } from "../types.js";
export declare function loadSpriteFrames(spriteName: string, animationName: string, width: number, direction?: string): Promise<FrameSet>;
export declare function loadStaticSpriteFrames(spriteName: string, width: number): Promise<FrameSet>;
export declare function loadConfig(): Promise<Config>;
/** Animation timer interface */
export interface AnimationTimer {
    start: () => void;
    stop: () => void;
    isRunning: () => boolean;
}
export declare function createAnimationTimer(intervalMs: number, onTick: () => void): AnimationTimer;
//# sourceMappingURL=sprites.d.ts.map