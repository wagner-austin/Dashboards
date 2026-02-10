/**
 * Tests for layer renderer with 3D projection.
 */
import { describe, it, expect } from "vitest";
import { renderAllLayers, renderForegroundLayers, _test_hooks } from "./renderer.js";
import { createSceneState } from "./types.js";
import { createProjectionConfig, createCamera } from "../world/Projection.js";
const { wrapEntityPosition, projectEntity, renderLayer, renderForegroundLayer, renderTiledForeground, WORLD_WIDTH, } = _test_hooks;
function createBuffer(width, height) {
    return Array.from({ length: height }, () => Array(width).fill(" "));
}
function createTestSizes() {
    return [
        { width: 3, frames: ["ABC\nDEF"] },
    ];
}
function createTestLayer(name, zIndex, layer, entities, positions = []) {
    const config = {
        name,
        type: "sprites",
        layer,
        spriteNames: [],
        positions,
        zIndex,
        tile: false,
    };
    return { config, entities };
}
function createTestEntity(worldX, worldZ) {
    return {
        spriteName: "test",
        sizes: createTestSizes(),
        sizeIdx: 0,
        frameIdx: 0,
        worldX,
        worldZ,
    };
}
describe("wrapEntityPosition", () => {
    it("does not wrap entity within half world width", () => {
        const entity = createTestEntity(100, 100);
        wrapEntityPosition(entity, 0);
        expect(entity.worldX).toBe(100);
    });
    it("wraps entity left when too far right of camera", () => {
        const entity = createTestEntity(500, 100);
        wrapEntityPosition(entity, 0);
        // 500 - 0 = 500 > 400 (half world), so wrap left
        expect(entity.worldX).toBe(500 - WORLD_WIDTH);
    });
    it("wraps entity right when too far left of camera", () => {
        const entity = createTestEntity(-500, 100);
        wrapEntityPosition(entity, 0);
        // -500 - 0 = -500 < -400 (half world), so wrap right
        expect(entity.worldX).toBe(-500 + WORLD_WIDTH);
    });
    it("follows camera position", () => {
        const entity = createTestEntity(1000, 100);
        // Camera at 600, entity at 1000
        // Relative = 1000 - 600 = 400, exactly at half world (no wrap)
        wrapEntityPosition(entity, 600);
        expect(entity.worldX).toBe(1000);
        // Camera at 599, entity at 1000
        // Relative = 1000 - 599 = 401 > 400, wrap left
        const entity2 = createTestEntity(1000, 100);
        wrapEntityPosition(entity2, 599);
        expect(entity2.worldX).toBe(1000 - WORLD_WIDTH);
    });
    it("wraps at exactly half world boundary", () => {
        const halfWorld = WORLD_WIDTH / 2;
        // At exactly half world, no wrap
        const entity1 = createTestEntity(halfWorld, 100);
        wrapEntityPosition(entity1, 0);
        expect(entity1.worldX).toBe(halfWorld);
        // Just past half world, wrap
        const entity2 = createTestEntity(halfWorld + 1, 100);
        wrapEntityPosition(entity2, 0);
        expect(entity2.worldX).toBe(halfWorld + 1 - WORLD_WIDTH);
    });
});
describe("projectEntity", () => {
    const config = createProjectionConfig();
    const camera = createCamera();
    const viewportWidth = 200;
    const viewportHeight = 100;
    it("returns visible for entity in valid depth range", () => {
        const entity = createTestEntity(100, 100);
        const screen = projectEntity(entity, camera, viewportWidth, viewportHeight, config);
        expect(screen.visible).toBe(true);
    });
    it("returns not visible for entity behind camera", () => {
        const entity = createTestEntity(100, 30);
        const screen = projectEntity(entity, camera, viewportWidth, viewportHeight, config);
        expect(screen.visible).toBe(false);
    });
    it("updates entity sizeIdx based on scale", () => {
        const sizes = [
            { width: 30, frames: ["small"] },
            { width: 50, frames: ["medium"] },
            { width: 80, frames: ["large"] },
        ];
        const entity = {
            spriteName: "test",
            sizes,
            sizeIdx: 0,
            frameIdx: 0,
            worldX: 100,
            worldZ: 100,
        };
        projectEntity(entity, camera, viewportWidth, viewportHeight, config);
        expect(entity.sizeIdx).toBeGreaterThanOrEqual(0);
        expect(entity.sizeIdx).toBeLessThan(sizes.length);
    });
    it("projects entity to screen center when aligned with camera X", () => {
        const entity = createTestEntity(0, 100);
        const screen = projectEntity(entity, camera, viewportWidth, viewportHeight, config);
        expect(screen.x).toBe(100);
    });
});
describe("renderLayer", () => {
    const config = createProjectionConfig();
    const camera = createCamera();
    const VIEWPORT_WIDTH = 100;
    const VIEWPORT_HEIGHT = 50;
    it("renders visible entities", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        const layer = createTestLayer("test", 0, 10, [entity]);
        renderLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("skips entities with invalid frames", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        entity.frameIdx = 99; // Invalid frame index - projectEntity doesn't change this
        const layer = createTestLayer("test", 0, 10, [entity]);
        renderLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("skips entities not visible", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 300);
        const layer = createTestLayer("test", 0, 30, [entity]);
        renderLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("handles empty layer", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const layer = createTestLayer("test", 0, 10, []);
        renderLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
    });
    it("wraps entities when positions are specified", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(500, 100);
        // Positions array makes it eligible for wrapping
        const layer = createTestLayer("test", 0, 10, [entity], [500]);
        // Camera at 0, entity at 500 which is > halfWorld (400)
        renderLayer(buffer, layer, { x: 0, z: 50 }, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        // Entity should have been wrapped
        expect(entity.worldX).toBe(500 - WORLD_WIDTH);
    });
    it("does not wrap entities without positions", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(500, 100);
        // No positions - single centered entity, no wrapping
        const layer = createTestLayer("test", 0, 10, [entity], []);
        renderLayer(buffer, layer, { x: 0, z: 50 }, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        // Entity should NOT have been wrapped
        expect(entity.worldX).toBe(500);
    });
});
describe("renderTiledForeground", () => {
    const camera = createCamera();
    const VIEWPORT_WIDTH = 100;
    const VIEWPORT_HEIGHT = 50;
    it("renders tiles across viewport width", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = {
            spriteName: "tile",
            sizes: [{ width: 10, frames: ["ABCDEFGHIJ\n1234567890"] }],
            sizeIdx: 0,
            frameIdx: 0,
            worldX: 0,
            worldZ: 100,
        };
        renderTiledForeground(buffer, entity, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("renders same content regardless of camera z", () => {
        const buffer1 = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const buffer2 = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = {
            spriteName: "tile",
            sizes: [{ width: 10, frames: ["ABCDEFGHIJ"] }],
            sizeIdx: 0,
            frameIdx: 0,
            worldX: 0,
            worldZ: 100,
        };
        renderTiledForeground(buffer1, entity, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        renderTiledForeground(buffer2, entity, { x: 0, z: 80 }, VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        // Both should render at bottom (fixed Y), content should be same
        const row1 = buffer1[VIEWPORT_HEIGHT - 1];
        const row2 = buffer2[VIEWPORT_HEIGHT - 1];
        expect(row1).toBeDefined();
        expect(row2).toBeDefined();
        expect(row1?.join("")).toBe(row2?.join(""));
    });
    it("handles invalid frame gracefully", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = {
            spriteName: "tile",
            sizes: [{ width: 10, frames: ["ABCDEFGHIJ"] }],
            sizeIdx: 0,
            frameIdx: 99,
            worldX: 0,
            worldZ: 100,
        };
        renderTiledForeground(buffer, entity, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
});
describe("renderForegroundLayer", () => {
    const config = createProjectionConfig();
    const camera = createCamera();
    const VIEWPORT_WIDTH = 100;
    const VIEWPORT_HEIGHT = 50;
    it("renders non-tiled entities", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        const layer = createTestLayer("grass-front", 0, 6, [entity]);
        renderForegroundLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("renders tiled layer with tiles", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = {
            spriteName: "tile",
            sizes: [{ width: 10, frames: ["ABCDEFGHIJ\n1234567890"] }],
            sizeIdx: 0,
            frameIdx: 0,
            worldX: 0,
            worldZ: 100,
        };
        const config2 = {
            name: "grass-front",
            type: "tile",
            layer: 6,
            spriteNames: ["tile"],
            positions: [],
            zIndex: 0,
            tile: true,
        };
        const layer = { config: config2, entities: [entity] };
        renderForegroundLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("handles empty tiled layer", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const config2 = {
            name: "grass-front",
            type: "tile",
            layer: 6,
            spriteNames: [],
            positions: [],
            zIndex: 0,
            tile: true,
        };
        const layer = { config: config2, entities: [] };
        renderForegroundLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
    });
    it("skips non-visible entities", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 300);
        const layer = createTestLayer("front", 0, 30, [entity]);
        renderForegroundLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("skips entities with invalid frame in non-tiled layer", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        entity.frameIdx = 99;
        const layer = createTestLayer("grass-front", 0, 6, [entity]);
        renderForegroundLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
});
describe("renderAllLayers", () => {
    const config = createProjectionConfig();
    const VIEWPORT_WIDTH = 100;
    const VIEWPORT_HEIGHT = 50;
    it("renders all non-front layers", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = createCamera();
        const entity = createTestEntity(0, 100);
        const layer = createTestLayer("background", 0, 15, [entity]);
        const scene = createSceneState([layer], camera);
        renderAllLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("skips layers with 'front' in name", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = createCamera();
        const entity = createTestEntity(0, 60);
        const layer = createTestLayer("grass-front", 0, 6, [entity]);
        const scene = createSceneState([layer], camera);
        renderAllLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("handles empty scene", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = createCamera();
        const scene = createSceneState([], camera);
        renderAllLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
    });
    it("uses scene camera for projection", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = { x: 50, z: 50 };
        const entity = createTestEntity(50, 100);
        const layer = createTestLayer("bg", 0, 10, [entity]);
        const scene = createSceneState([layer], camera);
        renderAllLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
});
describe("renderForegroundLayers", () => {
    const config = createProjectionConfig();
    const VIEWPORT_WIDTH = 100;
    const VIEWPORT_HEIGHT = 50;
    it("only renders layers with 'front' in name", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = createCamera();
        const bgEntity = createTestEntity(0, 100);
        const bgLayer = createTestLayer("background", 0, 15, [bgEntity]);
        const fgEntity = createTestEntity(0, 100);
        const fgLayer = createTestLayer("grass-front", 1, 6, [fgEntity]);
        const scene = createSceneState([bgLayer, fgLayer], camera);
        renderForegroundLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("handles empty scene", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = createCamera();
        const scene = createSceneState([], camera);
        renderForegroundLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
    });
});
describe("WORLD_WIDTH", () => {
    it("is 800", () => {
        expect(WORLD_WIDTH).toBe(800);
    });
});
//# sourceMappingURL=renderer.test.js.map