/**
 * Sprite management - loading frames and tracking state.
 */
import type { Sprite, Animation, FrameSet, Direction } from "../types.js";
/** Build the size key for looking up frame sets
 * For single-direction sprites: "50"
 * For multi-direction sprites: "50_left", "50_right"
 */
export declare function getSizeKey(size: number, direction: Direction, hasMultipleDirections: boolean): string;
/** Create a new sprite instance */
export declare function createSprite(name: string, animations: ReadonlyMap<string, Animation>, initialAnimation: string, initialSize: number, x: number, y: number): Sprite;
/** Advance to the next frame in the current animation */
export declare function advanceFrame(sprite: Sprite): void;
/** Switch to a different animation */
export declare function setAnimation(sprite: Sprite, animationName: string): void;
/** Switch to a different size (for depth effect) */
export declare function setSize(sprite: Sprite, size: number): void;
/** Set sprite direction */
export declare function setDirection(sprite: Sprite, direction: Direction): void;
/** Build an Animation from frame sets */
export declare function buildAnimation(name: string, sizes: Map<string, FrameSet>, directions: readonly Direction[]): Animation;
//# sourceMappingURL=Sprite.d.ts.map