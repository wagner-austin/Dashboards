import { describe, it, expect } from "vitest";
import {
  createSprite,
  advanceFrame,
  setAnimation,
  setSize,
  setDirection,
  buildAnimation,
  getSizeKey,
} from "./Sprite.js";
import type { Animation, FrameSet } from "../types.js";

function createTestAnimation(): Animation {
  const frameSet: FrameSet = {
    width: 50,
    frames: ["frame1", "frame2", "frame3"],
  };
  const sizes = new Map<string, FrameSet>();
  sizes.set("50", frameSet);
  return buildAnimation("test", sizes, ["right"]);
}

describe("createSprite", () => {
  it("should create a sprite with initial values", () => {
    const animations = new Map<string, Animation>();
    animations.set("walk", createTestAnimation());

    const sprite = createSprite("bunny", animations, "walk", 50, 10, 20);

    expect(sprite.name).toBe("bunny");
    expect(sprite.currentAnimation).toBe("walk");
    expect(sprite.currentFrame).toBe(0);
    expect(sprite.currentSize).toBe(50);
    expect(sprite.x).toBe(10);
    expect(sprite.y).toBe(20);
    expect(sprite.direction).toBe("right");
  });
});

describe("advanceFrame", () => {
  it("should advance to next frame", () => {
    const animations = new Map<string, Animation>();
    animations.set("walk", createTestAnimation());
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);

    advanceFrame(sprite);
    expect(sprite.currentFrame).toBe(1);

    advanceFrame(sprite);
    expect(sprite.currentFrame).toBe(2);
  });

  it("should wrap around to first frame", () => {
    const animations = new Map<string, Animation>();
    animations.set("walk", createTestAnimation());
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);

    advanceFrame(sprite);
    advanceFrame(sprite);
    advanceFrame(sprite);
    expect(sprite.currentFrame).toBe(0);
  });

  it("should do nothing if animation not found", () => {
    const animations = new Map<string, Animation>();
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);

    advanceFrame(sprite);
    expect(sprite.currentFrame).toBe(0);
  });

  it("should do nothing if frameSet not found for size", () => {
    const frameSet: FrameSet = {
      width: 50,
      frames: ["frame1", "frame2"],
    };
    const sizes = new Map<string, FrameSet>();
    sizes.set("50", frameSet);
    const animation = buildAnimation("walk", sizes, ["right"]);
    const animations = new Map<string, Animation>();
    animations.set("walk", animation);

    // Create sprite with size that doesn't exist in animation
    const sprite = createSprite("bunny", animations, "walk", 999, 0, 0);

    advanceFrame(sprite);
    expect(sprite.currentFrame).toBe(0);
  });

  it("should advance frame with multi-direction sprites", () => {
    const sizes = new Map<string, FrameSet>();
    sizes.set("50_left", { width: 50, frames: ["L1", "L2"] });
    sizes.set("50_right", { width: 50, frames: ["R1", "R2", "R3"] });
    const animation = buildAnimation("walk", sizes, ["left", "right"]);
    const animations = new Map<string, Animation>();
    animations.set("walk", animation);

    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);

    // Default direction is right
    advanceFrame(sprite);
    expect(sprite.currentFrame).toBe(1);
    advanceFrame(sprite);
    expect(sprite.currentFrame).toBe(2);
    advanceFrame(sprite);
    expect(sprite.currentFrame).toBe(0); // Wraps at 3 frames

    // Switch to left (2 frames)
    sprite.direction = "left";
    sprite.currentFrame = 0;
    advanceFrame(sprite);
    expect(sprite.currentFrame).toBe(1);
    advanceFrame(sprite);
    expect(sprite.currentFrame).toBe(0); // Wraps at 2 frames
  });
});

describe("setAnimation", () => {
  it("should switch animation and reset frame", () => {
    const animations = new Map<string, Animation>();
    animations.set("walk", createTestAnimation());
    animations.set("jump", createTestAnimation());
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);
    sprite.currentFrame = 2;

    setAnimation(sprite, "jump");

    expect(sprite.currentAnimation).toBe("jump");
    expect(sprite.currentFrame).toBe(0);
  });

  it("should do nothing if already on same animation", () => {
    const animations = new Map<string, Animation>();
    animations.set("walk", createTestAnimation());
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);
    sprite.currentFrame = 2;

    setAnimation(sprite, "walk");

    expect(sprite.currentFrame).toBe(2);
  });

  it("should do nothing if animation not found", () => {
    const animations = new Map<string, Animation>();
    animations.set("walk", createTestAnimation());
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);
    sprite.currentFrame = 2;

    setAnimation(sprite, "nonexistent");

    expect(sprite.currentAnimation).toBe("walk");
    expect(sprite.currentFrame).toBe(2);
  });
});

describe("setSize", () => {
  it("should set size to closest available", () => {
    const sizes = new Map<string, FrameSet>();
    sizes.set("30", { width: 30, frames: ["small"] });
    sizes.set("50", { width: 50, frames: ["medium"] });
    sizes.set("80", { width: 80, frames: ["large"] });
    const animation = buildAnimation("walk", sizes, ["right"]);

    const animations = new Map<string, Animation>();
    animations.set("walk", animation);
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);

    setSize(sprite, 45);
    expect(sprite.currentSize).toBe(50);

    setSize(sprite, 70);
    expect(sprite.currentSize).toBe(80);

    setSize(sprite, 35);
    expect(sprite.currentSize).toBe(30);
  });

  it("should do nothing if animation not found", () => {
    const animations = new Map<string, Animation>();
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);

    setSize(sprite, 100);

    expect(sprite.currentSize).toBe(50);
  });

  it("should do nothing if no sizes available", () => {
    const sizes = new Map<string, FrameSet>();
    const animation = buildAnimation("walk", sizes, ["right"]);
    const animations = new Map<string, Animation>();
    animations.set("walk", animation);
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);

    setSize(sprite, 100);

    expect(sprite.currentSize).toBe(50);
  });

  it("should handle exact size match", () => {
    const sizes = new Map<string, FrameSet>();
    sizes.set("50", { width: 50, frames: ["medium"] });
    const animation = buildAnimation("walk", sizes, ["right"]);
    const animations = new Map<string, Animation>();
    animations.set("walk", animation);
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);

    setSize(sprite, 50);

    expect(sprite.currentSize).toBe(50);
  });

  it("should handle directional size keys", () => {
    const sizes = new Map<string, FrameSet>();
    sizes.set("30_left", { width: 30, frames: ["small left"] });
    sizes.set("30_right", { width: 30, frames: ["small right"] });
    sizes.set("50_left", { width: 50, frames: ["medium left"] });
    sizes.set("50_right", { width: 50, frames: ["medium right"] });
    const animation = buildAnimation("walk", sizes, ["left", "right"]);

    const animations = new Map<string, Animation>();
    animations.set("walk", animation);
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);

    setSize(sprite, 35);
    expect(sprite.currentSize).toBe(30);

    setSize(sprite, 45);
    expect(sprite.currentSize).toBe(50);
  });
});

describe("setDirection", () => {
  it("should set sprite direction", () => {
    const animations = new Map<string, Animation>();
    const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);

    setDirection(sprite, "left");
    expect(sprite.direction).toBe("left");

    setDirection(sprite, "right");
    expect(sprite.direction).toBe("right");
  });
});

describe("buildAnimation", () => {
  it("should create animation with correct properties", () => {
    const sizes = new Map<string, FrameSet>();
    sizes.set("50", { width: 50, frames: ["frame1"] });

    const animation = buildAnimation("walk", sizes, ["left", "right"]);

    expect(animation.name).toBe("walk");
    expect(animation.sizes).toBe(sizes);
    expect(animation.directions).toEqual(["left", "right"]);
  });
});

describe("getSizeKey", () => {
  it("should return size only for single direction", () => {
    expect(getSizeKey(50, "left", false)).toBe("50");
    expect(getSizeKey(50, "right", false)).toBe("50");
  });

  it("should include direction for multiple directions", () => {
    expect(getSizeKey(50, "left", true)).toBe("50_left");
    expect(getSizeKey(50, "right", true)).toBe("50_right");
    expect(getSizeKey(30, "left", true)).toBe("30_left");
  });
});
