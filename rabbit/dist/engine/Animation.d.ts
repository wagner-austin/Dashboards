/**
 * Animation state machine and frame cycling.
 */
import type { BunnyState, Sprite } from "../types.js";
/** Animation controller for managing state transitions */
export declare class AnimationController {
    private readonly sprite;
    private state;
    private frameTimer;
    private readonly frameDelay;
    constructor(sprite: Sprite, initialState: BunnyState, fps: number);
    /** Get current state */
    getState(): BunnyState;
    /** Transition to a new state */
    setState(newState: BunnyState): void;
    /** Update animation frame based on elapsed time */
    update(deltaTime: number): void;
    /** Check if current animation has completed one cycle */
    isAnimationComplete(): boolean;
    /** Reset animation to first frame */
    reset(): void;
}
/** State machine for bunny behavior */
export declare class BunnyStateMachine {
    private readonly controller;
    private isJumping;
    private jumpVelocity;
    private readonly groundY;
    private readonly jumpStrength;
    private readonly gravity;
    constructor(controller: AnimationController, groundY: number, jumpStrength: number, gravity: number);
    /** Start a jump if not already jumping */
    jump(_sprite: Sprite): void;
    /** Update jump physics */
    updateJump(sprite: Sprite, deltaTime: number): void;
    /** Check if currently jumping */
    getIsJumping(): boolean;
    /** Start walking */
    walk(): void;
    /** Go to idle */
    idle(): void;
}
//# sourceMappingURL=Animation.d.ts.map