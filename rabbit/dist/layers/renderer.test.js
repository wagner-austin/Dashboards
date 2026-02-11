/**
 * Tests for layer renderer with 3D projection.
 */
import { describe, it, expect } from "vitest";
import { renderAllLayers, renderForegroundLayers, _test_hooks } from "./renderer.js";
import { createSceneState, createRenderCandidate } from "./types.js";
import { createProjectionConfig, createCamera, DEFAULT_WRAP_ITERATIONS, WORLD_WIDTH } from "../world/Projection.js";
import { LAYER_BEHAVIORS } from "../types.js";
const { wrapEntityPosition, getWrappedZPositions, renderEntityAtZ, renderEntitiesDepthSorted, renderLayer, renderForegroundLayer, renderTiledForeground, collectWrappedCandidates, collectDirectCandidates, compareByDepth, renderCandidate, collectLayerCandidates, } = _test_hooks;
/** Test depth bounds using visibleDepth as range (160) */
function createTestDepthBounds() {
    // visibleDepth = farZ - nearZ = 200 - 40 = 160
    return { minZ: -110, maxZ: 50, range: 160 };
}
function createBuffer(width, height) {
    return Array.from({ length: height }, () => Array(width).fill(" "));
}
function createTestSizes() {
    return [
        { width: 3, frames: ["ABC\nDEF"] },
    ];
}
function createTestLayer(name, zIndex, layer, entities, positions = [], behavior = LAYER_BEHAVIORS.midground) {
    const config = {
        name,
        type: "sprites",
        layer,
        spriteNames: [],
        positions,
        zIndex,
        tile: false,
        behavior,
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
describe("getWrappedZPositions", () => {
    const config = createProjectionConfig();
    const visibleDepth = config.farZ - config.nearZ;
    const expectedCount = 2 * config.wrapIterations + 1;
    it("returns positions based on wrapIterations from config", () => {
        const positions = getWrappedZPositions(100, config);
        expect(positions.length).toBe(expectedCount);
    });
    it("returns positions in back-to-front order (highest Z first)", () => {
        const positions = getWrappedZPositions(100, config);
        expect(positions[0]).toBe(100 + config.wrapIterations * visibleDepth);
        expect(positions[config.wrapIterations]).toBe(100);
        expect(positions[expectedCount - 1]).toBe(100 - config.wrapIterations * visibleDepth);
    });
    it("generates positions at visible depth spacing", () => {
        const positions = getWrappedZPositions(100, config);
        for (let i = 0; i < expectedCount - 1; i++) {
            const diff = (positions[i] ?? 0) - (positions[i + 1] ?? 0);
            expect(diff).toBe(visibleDepth);
        }
    });
    it("handles negative worldZ", () => {
        const positions = getWrappedZPositions(-50, config);
        expect(positions[0]).toBe(-50 + config.wrapIterations * visibleDepth);
        expect(positions[config.wrapIterations]).toBe(-50);
        expect(positions[expectedCount - 1]).toBe(-50 - config.wrapIterations * visibleDepth);
    });
    it("handles zero worldZ", () => {
        const positions = getWrappedZPositions(0, config);
        expect(positions[0]).toBe(config.wrapIterations * visibleDepth);
        expect(positions[config.wrapIterations]).toBe(0);
        expect(positions[expectedCount - 1]).toBe(-config.wrapIterations * visibleDepth);
    });
    it("respects custom wrapIterations in config", () => {
        const customConfig = { ...config, wrapIterations: 3 };
        const customVisibleDepth = customConfig.farZ - customConfig.nearZ;
        const positions = getWrappedZPositions(100, customConfig);
        expect(positions.length).toBe(2 * customConfig.wrapIterations + 1);
        expect(positions[0]).toBe(100 + customConfig.wrapIterations * customVisibleDepth);
        expect(positions[customConfig.wrapIterations]).toBe(100);
    });
    it("uses visible depth (farZ - nearZ) as wrap interval", () => {
        const positions = getWrappedZPositions(100, config);
        const interval = (positions[0] ?? 0) - (positions[1] ?? 0);
        expect(interval).toBe(config.farZ - config.nearZ);
    });
});
describe("DEFAULT_WRAP_ITERATIONS", () => {
    it("is 2 for minimal coverage", () => {
        expect(DEFAULT_WRAP_ITERATIONS).toBe(2);
    });
});
describe("renderEntityAtZ", () => {
    const config = createProjectionConfig();
    const camera = createCamera();
    const VIEWPORT_WIDTH = 100;
    const VIEWPORT_HEIGHT = 50;
    it("renders entity at specified Z position", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        renderEntityAtZ(buffer, entity, 100, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("does not render when Z position is not visible", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        // Render at Z=300 which is beyond visible range
        renderEntityAtZ(buffer, entity, 300, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("does not render when frame is invalid", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        entity.frameIdx = 99;
        renderEntityAtZ(buffer, entity, 100, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("updates entity sizeIdx based on scale", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
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
            worldX: 0,
            worldZ: 100,
        };
        renderEntityAtZ(buffer, entity, 100, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        expect(entity.sizeIdx).toBeGreaterThanOrEqual(0);
        expect(entity.sizeIdx).toBeLessThan(sizes.length);
    });
});
describe("renderEntitiesDepthSorted", () => {
    const config = createProjectionConfig();
    const camera = createCamera();
    const VIEWPORT_WIDTH = 100;
    const VIEWPORT_HEIGHT = 50;
    it("renders entities without wrapping when shouldWrapZ is false", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        renderEntitiesDepthSorted(buffer, [entity], camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config, false);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("renders entities with wrapping when shouldWrapZ is true", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        renderEntitiesDepthSorted(buffer, [entity], camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config, true);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("handles empty entity list", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        renderEntitiesDepthSorted(buffer, [], camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config, true);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("renders multiple entities in depth order", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entityNear = createTestEntity(0, 100);
        const entityFar = createTestEntity(10, 150);
        renderEntitiesDepthSorted(buffer, [entityNear, entityFar], camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config, false);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
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
        entity.frameIdx = 99; // Invalid frame index
        const layer = createTestLayer("test", 0, 10, [entity]);
        renderLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("skips entities not visible at any wrapped position", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        // Entity at Z=1000 - far beyond any wrapped position that could be visible
        const entity = createTestEntity(0, 1000);
        const layer = createTestLayer("test", 0, 30, [entity], [], LAYER_BEHAVIORS.static);
        renderLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("handles empty layer", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const layer = createTestLayer("test", 0, 10, []);
        renderLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
    });
    it("wraps entities with wrapX behavior", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(500, 100);
        // Midground behavior has wrapX: true
        const layer = createTestLayer("test", 0, 10, [entity], [], LAYER_BEHAVIORS.midground);
        // Camera at 0, entity at 500 which is > halfWorld (400)
        renderLayer(buffer, layer, { x: 0, z: 50 }, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        // Entity X should have been wrapped (mutation still used for X)
        expect(entity.worldX).toBe(500 - WORLD_WIDTH);
    });
    it("does not wrap entities with static behavior", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(500, 100);
        // Static behavior has wrapX: false
        const layer = createTestLayer("test", 0, 10, [entity], [], LAYER_BEHAVIORS.static);
        renderLayer(buffer, layer, { x: 0, z: 50 }, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        // Entity should NOT have been wrapped
        expect(entity.worldX).toBe(500);
    });
    it("renders at multiple Z positions with wrapZ behavior", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        // Entity at Z=100 should be visible at original position
        const entity = createTestEntity(0, 100);
        // Midground behavior has wrapZ: true
        const layer = createTestLayer("test", 0, 10, [entity], [], LAYER_BEHAVIORS.midground);
        renderLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        // Entity should be rendered (wrapZ doesn't mutate, just renders at multiple positions)
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
        // worldZ unchanged - multi-position rendering doesn't mutate
        expect(entity.worldZ).toBe(100);
    });
    it("renders only at original Z with static behavior", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        // Static behavior has wrapZ: false
        const layer = createTestLayer("test", 0, 10, [entity], [], LAYER_BEHAVIORS.static);
        renderLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        // Entity should be rendered at original position
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
        expect(entity.worldZ).toBe(100);
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
            behavior: LAYER_BEHAVIORS.foreground,
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
            behavior: LAYER_BEHAVIORS.foreground,
        };
        const layer = { config: config2, entities: [] };
        renderForegroundLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
    });
    it("skips non-visible entities when wrapZ is false", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 300);
        // Use foreground behavior (wrapZ=false) so entity is truly not visible
        const layer = createTestLayer("front", 0, 30, [entity], [], LAYER_BEHAVIORS.foreground);
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
    it("renders at multiple Z positions with wrapZ behavior in non-tiled layer", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        // Midground behavior has wrapZ: true
        const layer = createTestLayer("grass-front", 0, 6, [entity], [], LAYER_BEHAVIORS.midground);
        renderForegroundLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        // Entity should be rendered (wrapZ uses multi-position rendering)
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
        // worldZ unchanged - multi-position rendering doesn't mutate
        expect(entity.worldZ).toBe(100);
    });
    it("renders only at original Z in non-tiled layer with foreground behavior", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        // Foreground behavior has wrapZ: false
        const layer = createTestLayer("grass-front", 0, 6, [entity], [], LAYER_BEHAVIORS.foreground);
        renderForegroundLayer(buffer, layer, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        // Entity should be rendered at original position
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
        expect(entity.worldZ).toBe(100);
    });
});
describe("renderAllLayers", () => {
    const config = createProjectionConfig();
    const VIEWPORT_WIDTH = 100;
    const VIEWPORT_HEIGHT = 50;
    const depthBounds = createTestDepthBounds();
    it("renders all non-front layers", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = createCamera();
        const entity = createTestEntity(0, 100);
        const layer = createTestLayer("background", 0, 15, [entity]);
        const scene = createSceneState([layer], camera, depthBounds);
        renderAllLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("skips layers with 'front' in name", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = createCamera();
        const entity = createTestEntity(0, 60);
        const layer = createTestLayer("grass-front", 0, 6, [entity]);
        const scene = createSceneState([layer], camera, depthBounds);
        renderAllLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("handles empty scene", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = createCamera();
        const scene = createSceneState([], camera, depthBounds);
        renderAllLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
    });
    it("uses scene camera for projection", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = { x: 50, z: 50 };
        const entity = createTestEntity(50, 100);
        const layer = createTestLayer("bg", 0, 10, [entity]);
        const scene = createSceneState([layer], camera, depthBounds);
        renderAllLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
});
describe("renderForegroundLayers", () => {
    const config = createProjectionConfig();
    const VIEWPORT_WIDTH = 100;
    const VIEWPORT_HEIGHT = 50;
    const depthBounds = createTestDepthBounds();
    it("only renders layers with 'front' in name", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = createCamera();
        const bgEntity = createTestEntity(0, 100);
        const bgLayer = createTestLayer("background", 0, 15, [bgEntity]);
        const fgEntity = createTestEntity(0, 100);
        const fgLayer = createTestLayer("grass-front", 1, 6, [fgEntity]);
        const scene = createSceneState([bgLayer, fgLayer], camera, depthBounds);
        renderForegroundLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("handles empty scene", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const camera = createCamera();
        const scene = createSceneState([], camera, depthBounds);
        renderForegroundLayers(buffer, scene, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
    });
});
describe("collectWrappedCandidates", () => {
    const config = createProjectionConfig();
    const visibleDepth = config.farZ - config.nearZ;
    const candidatesPerEntity = 2 * config.wrapIterations + 1;
    it("collects candidates based on wrapIterations from config", () => {
        const entity = createTestEntity(0, 100);
        const candidates = collectWrappedCandidates([entity], config);
        expect(candidates.length).toBe(candidatesPerEntity);
    });
    it("creates candidates at all wrapped Z positions using visible depth", () => {
        const entity = createTestEntity(0, 100);
        const candidates = collectWrappedCandidates([entity], config);
        const zValues = candidates.map(c => c.effectiveZ);
        expect(zValues).toContain(100 + config.wrapIterations * visibleDepth);
        expect(zValues).toContain(100 + visibleDepth);
        expect(zValues).toContain(100);
        expect(zValues).toContain(100 - visibleDepth);
        expect(zValues).toContain(100 - config.wrapIterations * visibleDepth);
    });
    it("handles multiple entities", () => {
        const entity1 = createTestEntity(0, 100);
        const entity2 = createTestEntity(50, 150);
        const candidates = collectWrappedCandidates([entity1, entity2], config);
        expect(candidates.length).toBe(candidatesPerEntity * 2);
    });
    it("handles empty entity list", () => {
        const candidates = collectWrappedCandidates([], config);
        expect(candidates.length).toBe(0);
    });
    it("preserves entity reference in candidates", () => {
        const entity = createTestEntity(0, 100);
        const candidates = collectWrappedCandidates([entity], config);
        for (const candidate of candidates) {
            expect(candidate.entity).toBe(entity);
        }
    });
    it("respects custom wrapIterations in config", () => {
        const entity = createTestEntity(0, 100);
        const customConfig = { ...config, wrapIterations: 2 };
        const candidates = collectWrappedCandidates([entity], customConfig);
        expect(candidates.length).toBe(2 * customConfig.wrapIterations + 1);
    });
});
describe("collectDirectCandidates", () => {
    it("collects one candidate per entity", () => {
        const entity = createTestEntity(0, 100);
        const candidates = collectDirectCandidates([entity]);
        expect(candidates.length).toBe(1);
    });
    it("uses entity worldZ as effectiveZ", () => {
        const entity = createTestEntity(0, 150);
        const candidates = collectDirectCandidates([entity]);
        expect(candidates[0]?.effectiveZ).toBe(150);
    });
    it("handles multiple entities", () => {
        const entity1 = createTestEntity(0, 100);
        const entity2 = createTestEntity(50, 150);
        const candidates = collectDirectCandidates([entity1, entity2]);
        expect(candidates.length).toBe(2);
    });
    it("handles empty entity list", () => {
        const candidates = collectDirectCandidates([]);
        expect(candidates.length).toBe(0);
    });
    it("preserves entity reference in candidates", () => {
        const entity = createTestEntity(0, 100);
        const candidates = collectDirectCandidates([entity]);
        expect(candidates[0]?.entity).toBe(entity);
    });
});
describe("compareByDepth", () => {
    it("sorts higher Z before lower Z (back to front)", () => {
        const entity = createTestEntity(0, 100);
        const candidateA = createRenderCandidate(entity, 200);
        const candidateB = createRenderCandidate(entity, 100);
        expect(compareByDepth(candidateA, candidateB)).toBeLessThan(0);
    });
    it("sorts lower Z after higher Z", () => {
        const entity = createTestEntity(0, 100);
        const candidateA = createRenderCandidate(entity, 100);
        const candidateB = createRenderCandidate(entity, 200);
        expect(compareByDepth(candidateA, candidateB)).toBeGreaterThan(0);
    });
    it("returns zero for equal Z", () => {
        const entity = createTestEntity(0, 100);
        const candidateA = createRenderCandidate(entity, 150);
        const candidateB = createRenderCandidate(entity, 150);
        expect(compareByDepth(candidateA, candidateB)).toBe(0);
    });
    it("handles negative Z values", () => {
        const entity = createTestEntity(0, 100);
        const candidateA = createRenderCandidate(entity, -100);
        const candidateB = createRenderCandidate(entity, -200);
        expect(compareByDepth(candidateA, candidateB)).toBeLessThan(0);
    });
    it("sorts array correctly when used with Array.sort", () => {
        const entity = createTestEntity(0, 100);
        const candidates = [
            createRenderCandidate(entity, 50),
            createRenderCandidate(entity, 200),
            createRenderCandidate(entity, 100),
        ];
        candidates.sort(compareByDepth);
        expect(candidates[0]?.effectiveZ).toBe(200);
        expect(candidates[1]?.effectiveZ).toBe(100);
        expect(candidates[2]?.effectiveZ).toBe(50);
    });
});
describe("renderCandidate", () => {
    const config = createProjectionConfig();
    const camera = createCamera();
    const VIEWPORT_WIDTH = 100;
    const VIEWPORT_HEIGHT = 50;
    it("renders entity at candidate effectiveZ", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 999);
        const candidate = createRenderCandidate(entity, 100);
        renderCandidate(buffer, candidate, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const hasContent = buffer.some(row => row.some(c => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("does not render when effectiveZ is not visible", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        const candidate = createRenderCandidate(entity, 300);
        renderCandidate(buffer, candidate, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
    it("handles invalid frame gracefully", () => {
        const buffer = createBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
        const entity = createTestEntity(0, 100);
        entity.frameIdx = 99;
        const candidate = createRenderCandidate(entity, 100);
        renderCandidate(buffer, candidate, camera, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, config);
        const allEmpty = buffer.every(row => row.every(c => c === " "));
        expect(allEmpty).toBe(true);
    });
});
describe("collectLayerCandidates", () => {
    const config = createProjectionConfig();
    const camera = createCamera();
    it("applies X wrapping when layer has wrapX behavior", () => {
        const entity = createTestEntity(500, 100);
        // Midground behavior has wrapX: true
        const layer = createTestLayer("test", 0, 10, [entity], [], LAYER_BEHAVIORS.midground);
        collectLayerCandidates(layer, { x: 0, z: 50 }, config);
        // Entity should have been wrapped (500 > halfWorld 400)
        expect(entity.worldX).toBe(500 - WORLD_WIDTH);
    });
    it("skips X wrapping when layer has static behavior", () => {
        const entity = createTestEntity(500, 100);
        // Static behavior has wrapX: false
        const layer = createTestLayer("test", 0, 10, [entity], [], LAYER_BEHAVIORS.static);
        collectLayerCandidates(layer, { x: 0, z: 50 }, config);
        // Entity should NOT have been wrapped
        expect(entity.worldX).toBe(500);
    });
    it("returns wrapped candidates when layer has wrapZ behavior", () => {
        const entity = createTestEntity(0, 100);
        // Midground behavior has wrapZ: true
        const layer = createTestLayer("test", 0, 10, [entity], [], LAYER_BEHAVIORS.midground);
        const candidates = collectLayerCandidates(layer, camera, config);
        // Should have multiple candidates (wrapped)
        expect(candidates.length).toBe(2 * config.wrapIterations + 1);
    });
    it("returns direct candidates when layer has static behavior", () => {
        const entity = createTestEntity(0, 100);
        // Static behavior has wrapZ: false
        const layer = createTestLayer("test", 0, 10, [entity], [], LAYER_BEHAVIORS.static);
        const candidates = collectLayerCandidates(layer, camera, config);
        // Should have only one candidate (no wrapping)
        expect(candidates.length).toBe(1);
    });
    it("handles empty layer", () => {
        const layer = createTestLayer("test", 0, 10, [], [], LAYER_BEHAVIORS.midground);
        const candidates = collectLayerCandidates(layer, camera, config);
        expect(candidates.length).toBe(0);
    });
});
describe("WORLD_WIDTH", () => {
    it("is 800", () => {
        expect(WORLD_WIDTH).toBe(800);
    });
});
//# sourceMappingURL=renderer.test.js.map