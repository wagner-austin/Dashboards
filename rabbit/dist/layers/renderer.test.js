/**
 * Tests for layer renderer.
 */
import { describe, it, expect } from "vitest";
import { renderAllLayers, renderForegroundLayers, _test_hooks } from "./renderer.js";
import { createSceneState } from "./types.js";
const { getParallaxX, renderLayer } = _test_hooks;
const { renderForegroundLayer } = _test_hooks;
function createBuffer(width, height) {
    return Array.from({ length: height }, () => Array(width).fill(" "));
}
function createTestSizes() {
    return [
        { width: 3, frames: ["ABC\nDEF"] },
    ];
}
function createTestLayer(name, zIndex, parallax, entities) {
    const config = {
        name,
        type: "sprites",
        parallax,
        spriteNames: [],
        zIndex,
        tile: false,
    };
    return { config, entities };
}
function createTestEntity(x) {
    return {
        spriteName: "test",
        sizes: createTestSizes(),
        sizeIdx: 0,
        frameIdx: 0,
        x,
    };
}
describe("getParallaxX", () => {
    it("returns entity X when parallax is 0 (fixed)", () => {
        expect(getParallaxX(100, 50, 0.0)).toBe(100);
        expect(getParallaxX(100, 200, 0.0)).toBe(100);
    });
    it("returns full offset when parallax is 1 (foreground)", () => {
        expect(getParallaxX(100, 50, 1.0)).toBe(50);
        expect(getParallaxX(100, 0, 1.0)).toBe(100);
    });
    it("returns partial offset for intermediate parallax", () => {
        // entityX - floor(cameraX * parallax)
        // 100 - floor(100 * 0.5) = 100 - 50 = 50
        expect(getParallaxX(100, 100, 0.5)).toBe(50);
        // 100 - floor(100 * 0.2) = 100 - 20 = 80
        expect(getParallaxX(100, 100, 0.2)).toBe(80);
    });
    it("floors the parallax offset", () => {
        // 100 - floor(33 * 0.5) = 100 - floor(16.5) = 100 - 16 = 84
        expect(getParallaxX(100, 33, 0.5)).toBe(84);
    });
    it("handles negative camera positions", () => {
        // 100 - floor(-50 * 1.0) = 100 - (-50) = 150
        expect(getParallaxX(100, -50, 1.0)).toBe(150);
    });
});
describe("renderLayer", () => {
    // GROUND_TILE.length is 6, so viewport must be > 6 + sprite height for visibility
    const VIEWPORT_HEIGHT = 12;
    it("renders entities at parallax-adjusted positions", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const entity = createTestEntity(5);
        const layer = createTestLayer("test", 0, 0.0, [entity]);
        renderLayer(buffer, layer, 100, 10, VIEWPORT_HEIGHT);
        // With parallax 0, entity stays at x=5
        // Sprite is 2 rows, ground is 6 rows, viewport is 12
        // Y = 12 - 6 - 2 = 4
        expect(buffer[4]?.[5]).toBe("A");
        expect(buffer[4]?.[6]).toBe("B");
        expect(buffer[4]?.[7]).toBe("C");
    });
    it("applies parallax offset to entity position", () => {
        const buffer = createBuffer(15, VIEWPORT_HEIGHT);
        const entity = createTestEntity(10);
        const layer = createTestLayer("test", 0, 1.0, [entity]);
        // Camera at 5, parallax 1.0, entity at 10
        // screenX = 10 - floor(5 * 1.0) = 5
        renderLayer(buffer, layer, 5, 15, VIEWPORT_HEIGHT);
        // Y = 12 - 6 - 2 = 4
        expect(buffer[4]?.[5]).toBe("A");
    });
    it("renders multiple entities", () => {
        const buffer = createBuffer(20, VIEWPORT_HEIGHT);
        const entity1 = createTestEntity(0);
        const entity2 = createTestEntity(10);
        const layer = createTestLayer("test", 0, 0.0, [entity1, entity2]);
        renderLayer(buffer, layer, 0, 20, VIEWPORT_HEIGHT);
        // Y = 12 - 6 - 2 = 4
        expect(buffer[4]?.[0]).toBe("A");
        expect(buffer[4]?.[10]).toBe("A");
    });
    it("skips entities with invalid frames", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0);
        entity.sizeIdx = 99; // Invalid
        const layer = createTestLayer("test", 0, 0.0, [entity]);
        // Should not throw
        renderLayer(buffer, layer, 0, 10, VIEWPORT_HEIGHT);
        // Buffer should be unchanged (all spaces)
        const row4 = buffer[4];
        expect(row4?.every(c => c === " ")).toBe(true);
    });
    it("handles empty layer", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const layer = createTestLayer("test", 0, 0.0, []);
        // Should not throw
        renderLayer(buffer, layer, 0, 10, VIEWPORT_HEIGHT);
    });
});
describe("renderForegroundLayer with tiled layers", () => {
    const VIEWPORT_HEIGHT = 12;
    function createTiledLayer(name, zIndex, parallax, entities) {
        const config = {
            name,
            type: "tile",
            parallax,
            spriteNames: [],
            zIndex,
            tile: true,
        };
        return { config, entities };
    }
    it("renders tiled layer with repeating tiles at bottom", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const entity = {
            spriteName: "tile",
            sizes: [{ width: 3, frames: ["TTT\n---"] }],
            sizeIdx: 0,
            frameIdx: 0,
            x: 0,
        };
        const layer = createTiledLayer("tiled-front", 0, 0.0, [entity]);
        renderForegroundLayer(buffer, layer, 0, 10, VIEWPORT_HEIGHT);
        // With viewportHeight 12 and frame height 2, screenY = 12 - 2 = 10
        // Row 10 (0-indexed) should have "T" characters
        // Tiles fill the viewport horizontally
        expect(buffer[10]?.some(c => c === "T")).toBe(true);
    });
    it("applies parallax offset to tiled layer start position", () => {
        const buffer = createBuffer(20, VIEWPORT_HEIGHT);
        const entity = {
            spriteName: "tile",
            sizes: [{ width: 3, frames: ["ABC\nDEF"] }],
            sizeIdx: 0,
            frameIdx: 0,
            x: 0,
        };
        const layer = createTiledLayer("tiled-front", 0, 0.5, [entity]);
        // Camera at 6, parallax 0.5 means offset = floor(6 * 0.5) = 3
        // startX = -(3 % 3) = 0
        renderForegroundLayer(buffer, layer, 6, 20, VIEWPORT_HEIGHT);
        // With viewportHeight 12 and frame height 2, screenY = 10
        expect(buffer[10]?.some(c => c === "A")).toBe(true);
    });
    it("handles tiled layer with parallax creating offset", () => {
        const buffer = createBuffer(20, VIEWPORT_HEIGHT);
        const entity = {
            spriteName: "tile",
            sizes: [{ width: 4, frames: ["ABCD\n1234"] }],
            sizeIdx: 0,
            frameIdx: 0,
            x: 0,
        };
        const layer = createTiledLayer("tiled-front", 0, 1.0, [entity]);
        // Camera at 5, parallax 1.0 means offset = 5
        // startX = -(5 % 4) = -1
        renderForegroundLayer(buffer, layer, 5, 20, VIEWPORT_HEIGHT);
        // With viewportHeight 12 and frame height 2, screenY = 10
        // Tiles start at x=-1, so position 0 should have "B" (second char)
        expect(buffer[10]?.some(c => c !== " ")).toBe(true);
    });
    it("handles tiled layer with empty entities", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const layer = createTiledLayer("tiled-front", 0, 0.0, []);
        // Should not throw with empty entities
        renderForegroundLayer(buffer, layer, 0, 10, VIEWPORT_HEIGHT);
    });
    it("handles tiled layer with invalid frame", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const entity = {
            spriteName: "tile",
            sizes: [{ width: 3, frames: ["ABC\nDEF"] }],
            sizeIdx: 99, // Invalid
            frameIdx: 0,
            x: 0,
        };
        const layer = createTiledLayer("tiled-front", 0, 0.0, [entity]);
        // Should not throw with invalid frame
        renderForegroundLayer(buffer, layer, 0, 10, VIEWPORT_HEIGHT);
    });
});
describe("renderAllLayers", () => {
    const VIEWPORT_HEIGHT = 12;
    it("renders layers in order", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        // Create two layers with entities at same position
        // Later layer should overwrite earlier
        const entity1 = createTestEntity(0);
        const layer1 = createTestLayer("back", 0, 0.0, [entity1]);
        // Create entity with different frame for visibility
        const entity2 = {
            spriteName: "test2",
            sizes: [{ width: 3, frames: ["XYZ\n123"] }],
            sizeIdx: 0,
            frameIdx: 0,
            x: 0,
        };
        const layer2 = createTestLayer("top", 1, 0.0, [entity2]);
        const scene = createSceneState([layer1, layer2]);
        renderAllLayers(buffer, scene, 10, VIEWPORT_HEIGHT);
        // Y = 12 - 6 - 2 = 4
        // Second layer overwrites first
        expect(buffer[4]?.[0]).toBe("X");
        expect(buffer[4]?.[1]).toBe("Y");
    });
    it("uses scene cameraX for parallax", () => {
        const buffer = createBuffer(15, VIEWPORT_HEIGHT);
        const entity = createTestEntity(10);
        const layer = createTestLayer("test", 0, 1.0, [entity]);
        const scene = createSceneState([layer]);
        scene.cameraX = 5;
        renderAllLayers(buffer, scene, 15, VIEWPORT_HEIGHT);
        // Y = 12 - 6 - 2 = 4, screenX = 10 - 5 = 5
        expect(buffer[4]?.[5]).toBe("A");
    });
    it("handles empty scene", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const scene = createSceneState([]);
        // Should not throw
        renderAllLayers(buffer, scene, 10, VIEWPORT_HEIGHT);
    });
    it("renders layers with different parallax values", () => {
        const buffer = createBuffer(20, VIEWPORT_HEIGHT);
        // Background layer: parallax 0.2
        const bgEntity = {
            spriteName: "bg",
            sizes: [{ width: 1, frames: ["B"] }],
            sizeIdx: 0,
            frameIdx: 0,
            x: 12,
        };
        const bgLayer = createTestLayer("bg", 0, 0.2, [bgEntity]);
        // Foreground layer: parallax 1.0
        const fgEntity = {
            spriteName: "fg",
            sizes: [{ width: 1, frames: ["F"] }],
            sizeIdx: 0,
            frameIdx: 0,
            x: 12,
        };
        const fgLayer = createTestLayer("fg", 1, 1.0, [fgEntity]);
        const scene = createSceneState([bgLayer, fgLayer]);
        scene.cameraX = 10;
        renderAllLayers(buffer, scene, 20, VIEWPORT_HEIGHT);
        // Y = 12 - 6 - 1 = 5 (single-line sprites)
        // Background: 12 - floor(10 * 0.2) = 12 - 2 = 10
        // Foreground: 12 - floor(10 * 1.0) = 12 - 10 = 2
        expect(buffer[5]?.[10]).toBe("B");
        expect(buffer[5]?.[2]).toBe("F");
    });
    it("skips layers with 'front' in name", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const entity = createTestEntity(5);
        const layer = createTestLayer("grass-front", 0, 1.0, [entity]);
        const scene = createSceneState([layer]);
        renderAllLayers(buffer, scene, 10, VIEWPORT_HEIGHT);
        // Should NOT render - layer has "front" in name
        const row4 = buffer[4];
        expect(row4?.every(c => c === " ")).toBe(true);
    });
});
describe("renderForegroundLayer", () => {
    const VIEWPORT_HEIGHT = 12;
    it("renders entities at bottom of screen", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const entity = createTestEntity(5);
        const layer = createTestLayer("grass-front", 0, 1.0, [entity]);
        renderForegroundLayer(buffer, layer, 0, 10, VIEWPORT_HEIGHT);
        // Y = viewportHeight - spriteHeight = 12 - 2 = 10
        expect(buffer[10]?.[5]).toBe("A");
        expect(buffer[10]?.[6]).toBe("B");
    });
    it("applies parallax to X position", () => {
        const buffer = createBuffer(15, VIEWPORT_HEIGHT);
        const entity = createTestEntity(10);
        const layer = createTestLayer("front", 0, 0.5, [entity]);
        // cameraX = 10, parallax = 0.5, entityX = 10
        // screenX = 10 - floor(10 * 0.5) = 5
        renderForegroundLayer(buffer, layer, 10, 15, VIEWPORT_HEIGHT);
        expect(buffer[10]?.[5]).toBe("A");
    });
    it("skips entities with invalid frames", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0);
        entity.sizeIdx = 99; // Invalid
        const layer = createTestLayer("front", 0, 1.0, [entity]);
        // Should not throw
        renderForegroundLayer(buffer, layer, 0, 10, VIEWPORT_HEIGHT);
    });
});
describe("renderForegroundLayers", () => {
    const VIEWPORT_HEIGHT = 12;
    it("only renders layers with 'front' in name", () => {
        const buffer = createBuffer(15, VIEWPORT_HEIGHT);
        // Background layer - should NOT render
        const bgEntity = {
            spriteName: "bg",
            sizes: [{ width: 1, frames: ["B"] }],
            sizeIdx: 0,
            frameIdx: 0,
            x: 5,
        };
        const bgLayer = createTestLayer("background", 0, 1.0, [bgEntity]);
        // Foreground layer - should render
        const fgEntity = {
            spriteName: "fg",
            sizes: [{ width: 1, frames: ["F"] }],
            sizeIdx: 0,
            frameIdx: 0,
            x: 10,
        };
        const fgLayer = createTestLayer("grass-front", 1, 1.0, [fgEntity]);
        const scene = createSceneState([bgLayer, fgLayer]);
        renderForegroundLayers(buffer, scene, 15, VIEWPORT_HEIGHT);
        // Y = 12 - 1 = 11 (at bottom)
        // Background should NOT be rendered
        expect(buffer[11]?.[5]).toBe(" ");
        // Foreground should be rendered
        expect(buffer[11]?.[10]).toBe("F");
    });
    it("handles empty scene", () => {
        const buffer = createBuffer(10, VIEWPORT_HEIGHT);
        const scene = createSceneState([]);
        // Should not throw
        renderForegroundLayers(buffer, scene, 10, VIEWPORT_HEIGHT);
    });
});
//# sourceMappingURL=renderer.test.js.map