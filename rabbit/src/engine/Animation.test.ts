import { describe, it, expect, beforeEach } from "vitest";
import { AnimationController, BunnyStateMachine } from "./Animation.js";
import { createSprite, buildAnimation } from "./Sprite.js";
import type { Animation, FrameSet, Sprite } from "../types.js";

function createTestSprite(): Sprite {
  const frameSet: FrameSet = {
    width: 50,
    frames: ["frame1", "frame2", "frame3"],
  };
  const sizes = new Map<string, FrameSet>();
  sizes.set("50", frameSet);
  const walkAnim = buildAnimation("walk", sizes, ["right"]);
  const jumpAnim = buildAnimation("jump", sizes, ["right"]);
  const idleAnim = buildAnimation("idle", sizes, ["right"]);

  const animations = new Map<string, Animation>();
  animations.set("walk", walkAnim);
  animations.set("jump", jumpAnim);
  animations.set("idle", idleAnim);

  return createSprite("bunny", animations, "walk", 50, 0, 0);
}

describe("AnimationController", () => {
  let sprite: Sprite;
  let controller: AnimationController;

  beforeEach(() => {
    sprite = createTestSprite();
    controller = new AnimationController(sprite, "walk", 10);
  });

  it("should initialize with correct state", () => {
    expect(controller.getState()).toBe("walk");
  });

  it("should transition to new state", () => {
    controller.setState("jump");
    expect(controller.getState()).toBe("jump");
    expect(sprite.currentAnimation).toBe("jump");
  });

  it("should not transition if already in state", () => {
    sprite.currentFrame = 2;
    controller.setState("walk");
    expect(sprite.currentFrame).toBe(2);
  });

  it("should advance frame on update", () => {
    controller.update(100);
    expect(sprite.currentFrame).toBe(1);
  });

  it("should not advance frame if not enough time passed", () => {
    controller.update(50);
    expect(sprite.currentFrame).toBe(0);
  });

  it("should detect animation complete", () => {
    sprite.currentFrame = 2;
    expect(controller.isAnimationComplete()).toBe(true);
  });

  it("should detect animation not complete", () => {
    sprite.currentFrame = 1;
    expect(controller.isAnimationComplete()).toBe(false);
  });

  it("should reset animation", () => {
    sprite.currentFrame = 2;
    controller.reset();
    expect(sprite.currentFrame).toBe(0);
  });

  it("should return true for isAnimationComplete when animation not found", () => {
    // Create sprite with empty animations map - "walk" won't be found
    const emptyAnimations = new Map<string, Animation>();
    const emptySprite = createSprite("test", emptyAnimations, "walk", 50, 0, 0);
    const ctrl = new AnimationController(emptySprite, "walk", 10);

    expect(ctrl.isAnimationComplete()).toBe(true);
  });

  it("should return true for isAnimationComplete when frameSet not found", () => {
    const frameSet: FrameSet = {
      width: 50,
      frames: ["frame1"],
    };
    const sizes = new Map<string, FrameSet>();
    sizes.set("50", frameSet);
    const animation = buildAnimation("walk", sizes, ["right"]);
    const animations = new Map<string, Animation>();
    animations.set("walk", animation);

    // Create sprite with size that doesn't exist
    const testSprite = createSprite("test", animations, "walk", 999, 0, 0);
    const ctrl = new AnimationController(testSprite, "walk", 10);

    expect(ctrl.isAnimationComplete()).toBe(true);
  });
});

describe("BunnyStateMachine", () => {
  let sprite: Sprite;
  let controller: AnimationController;
  let stateMachine: BunnyStateMachine;

  beforeEach(() => {
    sprite = createTestSprite();
    sprite.y = 100;
    controller = new AnimationController(sprite, "walk", 10);
    stateMachine = new BunnyStateMachine(controller, 100, 300, 800);
  });

  it("should start jump", () => {
    stateMachine.jump(sprite);
    expect(stateMachine.getIsJumping()).toBe(true);
    expect(controller.getState()).toBe("jump");
  });

  it("should not double jump", () => {
    stateMachine.jump(sprite);
    const initialY = sprite.y;
    stateMachine.updateJump(sprite, 100);
    const midJumpY = sprite.y;
    expect(midJumpY).not.toBe(initialY);
    stateMachine.jump(sprite);
    expect(stateMachine.getIsJumping()).toBe(true);
  });

  it("should land after jump", () => {
    stateMachine.jump(sprite);
    stateMachine.updateJump(sprite, 1000);
    expect(stateMachine.getIsJumping()).toBe(false);
    expect(sprite.y).toBe(100);
    expect(controller.getState()).toBe("walk");
  });

  it("should walk when not jumping", () => {
    stateMachine.walk();
    expect(controller.getState()).toBe("walk");
  });

  it("should not walk while jumping", () => {
    stateMachine.jump(sprite);
    stateMachine.walk();
    expect(controller.getState()).toBe("jump");
  });

  it("should go idle when not jumping", () => {
    stateMachine.idle();
    expect(controller.getState()).toBe("idle");
  });

  it("should not go idle while jumping", () => {
    stateMachine.jump(sprite);
    stateMachine.idle();
    expect(controller.getState()).toBe("jump");
  });

  it("should do nothing on updateJump when not jumping", () => {
    const initialY = sprite.y;
    stateMachine.updateJump(sprite, 100);
    expect(sprite.y).toBe(initialY);
  });

  it("should apply gravity during jump", () => {
    stateMachine.jump(sprite);
    const y1 = sprite.y;
    stateMachine.updateJump(sprite, 16); // ~60fps frame
    const y2 = sprite.y;

    // First update should move up (negative velocity)
    expect(y2).toBeLessThan(y1);
  });
});
