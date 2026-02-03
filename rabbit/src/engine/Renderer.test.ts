import { describe, it, expect, beforeEach } from "vitest";
import { Renderer } from "./Renderer.js";
import { createSprite, buildAnimation } from "./Sprite.js";
import { createLayer, addSprite } from "./Layer.js";
import type { Animation, FrameSet } from "../types.js";

describe("Renderer", () => {
  let mockElement: HTMLPreElement;
  let renderer: Renderer;

  beforeEach(() => {
    mockElement = {
      textContent: "",
    } as HTMLPreElement;
    renderer = new Renderer(10, 5, mockElement);
  });

  it("should create a buffer of correct dimensions", () => {
    expect(renderer.getWidth()).toBe(10);
    expect(renderer.getHeight()).toBe(5);
  });

  it("should clear buffer to spaces", () => {
    renderer.clear();
    renderer.render();
    const content = mockElement.textContent;
    expect(content).not.toBeNull();
    const lines = content.split("\n");
    expect(lines[0]).toBe("          ");
  });

  it("should render buffer to element", () => {
    renderer.clear();
    renderer.render();
    const content = mockElement.textContent;
    expect(content).not.toBeNull();
    expect(content.length).toBeGreaterThan(0);
  });

  describe("drawSprite", () => {
    it("should draw sprite frame to buffer", () => {
      const frameSet: FrameSet = {
        width: 3,
        frames: ["###\n# #\n###"],
      };
      const sizes = new Map<string, FrameSet>();
      sizes.set("50", frameSet);
      const animation = buildAnimation("test", sizes, ["right"]);
      const animations = new Map<string, Animation>();
      animations.set("test", animation);
      const sprite = createSprite("box", animations, "test", 50, 1, 1);

      renderer.clear();
      renderer.drawSprite(sprite);
      renderer.render();

      const content = mockElement.textContent;
      expect(content).toContain("#");
    });

    it("should skip spaces in sprite frame", () => {
      const frameSet: FrameSet = {
        width: 3,
        frames: ["# #"],
      };
      const sizes = new Map<string, FrameSet>();
      sizes.set("50", frameSet);
      const animation = buildAnimation("test", sizes, ["right"]);
      const animations = new Map<string, Animation>();
      animations.set("test", animation);
      const sprite = createSprite("box", animations, "test", 50, 0, 0);

      renderer.clear();
      renderer.drawSprite(sprite);
      renderer.render();

      const content = mockElement.textContent;
      const firstLine = content.split("\n")[0];
      // Frame is "# #" - both # are drawn, middle space is transparent
      expect(firstLine).toBe("# #       ");
    });

    it("should clip sprite at buffer edges", () => {
      const frameSet: FrameSet = {
        width: 5,
        frames: ["#####\n#####\n#####"],
      };
      const sizes = new Map<string, FrameSet>();
      sizes.set("50", frameSet);
      const animation = buildAnimation("test", sizes, ["right"]);
      const animations = new Map<string, Animation>();
      animations.set("test", animation);
      // Position sprite partially off-screen
      const sprite = createSprite("box", animations, "test", 50, 8, 3);

      renderer.clear();
      renderer.drawSprite(sprite);
      renderer.render();

      // Should not throw and should clip properly
      const content = mockElement.textContent;
      expect(content).not.toBeNull();
    });

    it("should handle sprite with missing animation", () => {
      const animations = new Map<string, Animation>();
      const sprite = createSprite("box", animations, "nonexistent", 50, 0, 0);

      renderer.clear();
      renderer.drawSprite(sprite);
      renderer.render();

      // Should not throw
      const content = mockElement.textContent;
      expect(content).not.toBeNull();
    });

    it("should handle sprite with missing frameSet for size", () => {
      const frameSet: FrameSet = {
        width: 3,
        frames: ["###"],
      };
      const sizes = new Map<string, FrameSet>();
      sizes.set("50", frameSet);
      const animation = buildAnimation("test", sizes, ["right"]);
      const animations = new Map<string, Animation>();
      animations.set("test", animation);
      // Request size that doesn't exist
      const sprite = createSprite("box", animations, "test", 999, 0, 0);

      renderer.clear();
      renderer.drawSprite(sprite);
      renderer.render();

      // Should not throw
      const content = mockElement.textContent;
      expect(content).not.toBeNull();
    });

    it("should handle sprite with missing frame", () => {
      const frameSet: FrameSet = {
        width: 3,
        frames: [],
      };
      const sizes = new Map<string, FrameSet>();
      sizes.set("50", frameSet);
      const animation = buildAnimation("test", sizes, ["right"]);
      const animations = new Map<string, Animation>();
      animations.set("test", animation);
      const sprite = createSprite("box", animations, "test", 50, 0, 0);

      renderer.clear();
      renderer.drawSprite(sprite);
      renderer.render();

      // Should not throw
      const content = mockElement.textContent;
      expect(content).not.toBeNull();
    });

    it("should handle negative sprite positions", () => {
      const frameSet: FrameSet = {
        width: 3,
        frames: ["###\n###\n###"],
      };
      const sizes = new Map<string, FrameSet>();
      sizes.set("50", frameSet);
      const animation = buildAnimation("test", sizes, ["right"]);
      const animations = new Map<string, Animation>();
      animations.set("test", animation);
      const sprite = createSprite("box", animations, "test", 50, -1, -1);

      renderer.clear();
      renderer.drawSprite(sprite);
      renderer.render();

      // Should clip and not throw
      const content = mockElement.textContent;
      expect(content).not.toBeNull();
    });

    it("should use direction for multi-direction sprites", () => {
      const sizes = new Map<string, FrameSet>();
      sizes.set("50_left", { width: 1, frames: ["L"] });
      sizes.set("50_right", { width: 1, frames: ["R"] });
      const animation = buildAnimation("test", sizes, ["left", "right"]);
      const animations = new Map<string, Animation>();
      animations.set("test", animation);

      const sprite = createSprite("box", animations, "test", 50, 0, 0);
      sprite.direction = "right";

      renderer.clear();
      renderer.drawSprite(sprite);
      renderer.render();

      let content = mockElement.textContent;
      expect(content).toContain("R");

      // Change direction
      sprite.direction = "left";
      renderer.clear();
      renderer.drawSprite(sprite);
      renderer.render();

      content = mockElement.textContent;
      expect(content).toContain("L");
    });
  });

  describe("drawLayer", () => {
    it("should draw all sprites in layer", () => {
      const frameSet: FrameSet = {
        width: 1,
        frames: ["#"],
      };
      const sizes = new Map<string, FrameSet>();
      sizes.set("50", frameSet);
      const animation = buildAnimation("test", sizes, ["right"]);
      const animations = new Map<string, Animation>();
      animations.set("test", animation);

      const sprite1 = createSprite("a", animations, "test", 50, 0, 0);
      const sprite2 = createSprite("b", animations, "test", 50, 2, 0);

      const layer = createLayer("foreground", 1.0);
      addSprite(layer, sprite1);
      addSprite(layer, sprite2);

      renderer.clear();
      renderer.drawLayer(layer);
      renderer.render();

      const content = mockElement.textContent;
      const lines = content.split("\n");
      expect(lines.length).toBeGreaterThan(0);
      const firstLine = lines[0];
      if (firstLine === undefined) {
        throw new Error("firstLine should not be undefined");
      }
      expect(firstLine[0]).toBe("#");
      expect(firstLine[2]).toBe("#");
    });
  });
});
