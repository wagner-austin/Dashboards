/**
 * Animation state machine and frame cycling.
 */
import { setAnimation, advanceFrame, getSizeKey } from "./Sprite.js";
/** Animation controller for managing state transitions */
export class AnimationController {
    sprite;
    state;
    frameTimer;
    frameDelay;
    constructor(sprite, initialState, fps) {
        this.sprite = sprite;
        this.state = initialState;
        this.frameTimer = 0;
        this.frameDelay = 1000 / fps;
    }
    /** Get current state */
    getState() {
        return this.state;
    }
    /** Transition to a new state */
    setState(newState) {
        if (this.state === newState)
            return;
        this.state = newState;
        setAnimation(this.sprite, newState);
    }
    /** Update animation frame based on elapsed time */
    update(deltaTime) {
        this.frameTimer += deltaTime;
        if (this.frameTimer >= this.frameDelay) {
            this.frameTimer -= this.frameDelay;
            advanceFrame(this.sprite);
        }
    }
    /** Check if current animation has completed one cycle */
    isAnimationComplete() {
        const animation = this.sprite.animations.get(this.sprite.currentAnimation);
        if (animation === undefined)
            return true;
        const hasMultipleDirections = animation.directions.length > 1;
        const key = getSizeKey(this.sprite.currentSize, this.sprite.direction, hasMultipleDirections);
        const frameSet = animation.sizes.get(key);
        if (frameSet === undefined)
            return true;
        return this.sprite.currentFrame === frameSet.frames.length - 1;
    }
    /** Reset animation to first frame */
    reset() {
        this.sprite.currentFrame = 0;
        this.frameTimer = 0;
    }
}
/** State machine for bunny behavior */
export class BunnyStateMachine {
    controller;
    isJumping;
    jumpVelocity;
    groundY;
    jumpStrength;
    gravity;
    constructor(controller, groundY, jumpStrength, gravity) {
        this.controller = controller;
        this.isJumping = false;
        this.jumpVelocity = 0;
        this.groundY = groundY;
        this.jumpStrength = jumpStrength;
        this.gravity = gravity;
    }
    /** Start a jump if not already jumping */
    jump(_sprite) {
        if (this.isJumping)
            return;
        this.isJumping = true;
        this.jumpVelocity = -this.jumpStrength;
        this.controller.setState("jump");
    }
    /** Update jump physics */
    updateJump(sprite, deltaTime) {
        if (!this.isJumping)
            return;
        const dt = deltaTime / 1000;
        this.jumpVelocity += this.gravity * dt;
        sprite.y += this.jumpVelocity * dt;
        if (sprite.y >= this.groundY) {
            sprite.y = this.groundY;
            this.isJumping = false;
            this.jumpVelocity = 0;
            this.controller.setState("walk");
        }
    }
    /** Check if currently jumping */
    getIsJumping() {
        return this.isJumping;
    }
    /** Start walking */
    walk() {
        if (this.isJumping)
            return;
        this.controller.setState("walk");
    }
    /** Go to idle */
    idle() {
        if (this.isJumping)
            return;
        this.controller.setState("idle");
    }
}
//# sourceMappingURL=Animation.js.map