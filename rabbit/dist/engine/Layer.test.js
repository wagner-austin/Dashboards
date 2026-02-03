import { describe, it, expect } from "vitest";
import { createLayer, addSprite, removeSprite, getSprites, updateLayerPosition, } from "./Layer.js";
import { createSprite } from "./Sprite.js";
describe("createLayer", () => {
    it("should create a layer with name and parallax", () => {
        const layer = createLayer("background", 0.5);
        expect(layer.name).toBe("background");
        expect(layer.parallax).toBe(0.5);
        expect(layer.sprites).toEqual([]);
    });
});
describe("addSprite", () => {
    it("should add sprite to layer", () => {
        const layer = createLayer("foreground", 1.0);
        const animations = new Map();
        const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);
        addSprite(layer, sprite);
        expect(layer.sprites).toHaveLength(1);
        expect(layer.sprites[0]).toBe(sprite);
    });
});
describe("removeSprite", () => {
    it("should remove sprite from layer by name", () => {
        const layer = createLayer("foreground", 1.0);
        const animations = new Map();
        const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);
        addSprite(layer, sprite);
        removeSprite(layer, "bunny");
        expect(layer.sprites).toHaveLength(0);
    });
    it("should do nothing if sprite not found", () => {
        const layer = createLayer("foreground", 1.0);
        const animations = new Map();
        const sprite = createSprite("bunny", animations, "walk", 50, 0, 0);
        addSprite(layer, sprite);
        removeSprite(layer, "notfound");
        expect(layer.sprites).toHaveLength(1);
    });
});
describe("getSprites", () => {
    it("should return all sprites in layer", () => {
        const layer = createLayer("foreground", 1.0);
        const animations = new Map();
        const sprite1 = createSprite("bunny", animations, "walk", 50, 0, 0);
        const sprite2 = createSprite("tree", animations, "idle", 50, 100, 0);
        addSprite(layer, sprite1);
        addSprite(layer, sprite2);
        const sprites = getSprites(layer);
        expect(sprites).toHaveLength(2);
    });
});
describe("updateLayerPosition", () => {
    it("should update sprite positions based on parallax", () => {
        const layer = createLayer("background", 0.5);
        const animations = new Map();
        const sprite = createSprite("tree", animations, "idle", 50, 100, 0);
        addSprite(layer, sprite);
        updateLayerPosition(layer, 10, 0);
        // With parallax 0.5 and cameraX 10, sprite should move by -5
        expect(sprite.x).toBe(95);
    });
    it("should move sprites at full parallax", () => {
        const layer = createLayer("foreground", 1.0);
        const animations = new Map();
        const sprite = createSprite("bunny", animations, "walk", 50, 50, 0);
        addSprite(layer, sprite);
        updateLayerPosition(layer, 20, 0);
        // With parallax 1.0 and cameraX 20, sprite should move by -20
        expect(sprite.x).toBe(30);
    });
    it("should not move static sprites (parallax 0)", () => {
        const layer = createLayer("sky", 0);
        const animations = new Map();
        const sprite = createSprite("cloud", animations, "idle", 50, 100, 0);
        addSprite(layer, sprite);
        updateLayerPosition(layer, 100, 0);
        // With parallax 0, sprite should not move
        expect(sprite.x).toBe(100);
    });
    it("should update all sprites in layer", () => {
        const layer = createLayer("midground", 0.5);
        const animations = new Map();
        const sprite1 = createSprite("tree1", animations, "idle", 50, 100, 0);
        const sprite2 = createSprite("tree2", animations, "idle", 50, 200, 0);
        addSprite(layer, sprite1);
        addSprite(layer, sprite2);
        updateLayerPosition(layer, 10, 0);
        expect(sprite1.x).toBe(95);
        expect(sprite2.x).toBe(195);
    });
});
//# sourceMappingURL=Layer.test.js.map