/**
 * @vitest-environment jsdom
 * Tests for scene renderer.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderFrame, _test_hooks } from "./SceneRenderer.js";
const { bunnyWorldZ, drawBunny } = _test_hooks;
import { createInitialBunnyState } from "../entities/Bunny.js";
import { createSceneState } from "../layers/index.js";
import { createCamera, createProjectionConfig } from "../world/Projection.js";
import { createTestEntity, createTestLayer, createTestSizes } from "../testing/fixtures.js";
/** Test depth bounds (minZ=-110, maxZ=160, range=270) */
function createTestDepthBounds() {
    return { minZ: -110, maxZ: 160, range: 270 };
}
function createTestBunnyFrames() {
    return {
        walkLeft: ["walk_l_0", "walk_l_1"],
        walkRight: ["walk_r_0", "walk_r_1"],
        jumpLeft: ["jump_l_0"],
        jumpRight: ["jump_r_0"],
        idleLeft: ["idle_l_0"],
        idleRight: ["idle_r_0"],
        walkToIdleLeft: ["trans_l_0", "trans_l_1"],
        walkToIdleRight: ["trans_r_0", "trans_r_1"],
        walkToTurnAwayLeft: ["turn_away_l_0", "turn_away_l_1"],
        walkToTurnAwayRight: ["turn_away_r_0", "turn_away_r_1"],
        walkToTurnTowardLeft: ["turn_toward_l_0", "turn_toward_l_1"],
        walkToTurnTowardRight: ["turn_toward_r_0", "turn_toward_r_1"],
        hopAway: ["hop_away_0", "hop_away_1"],
        hopToward: ["hop_toward_0", "hop_toward_1"],
    };
}
function createTestBunnyState(animation, facingRight = false) {
    return { facingRight, animation };
}
function createTestSceneState() {
    return createSceneState([], createCamera(), createTestDepthBounds());
}
describe("renderFrame", () => {
    let screen;
    const projectionConfig = createProjectionConfig();
    beforeEach(() => {
        screen = document.createElement("pre");
        document.body.appendChild(screen);
    });
    afterEach(() => {
        document.body.removeChild(screen);
    });
    it("renders frame and returns updated state", () => {
        const bunnyState = createInitialBunnyState();
        const sceneState = createTestSceneState();
        const renderState = {
            bunnyState,
            sceneState,
            viewport: { width: 80, height: 24, charW: 10, charH: 20 },
            lastTime: 0,
            projectionConfig,
        };
        const bunnyFrames = createTestBunnyFrames();
        const result = renderFrame(renderState, bunnyFrames, screen, 1000);
        expect(result.lastTime).toBe(1000);
        expect(screen.textContent).not.toBe("");
        expect(screen.textContent.length).toBeGreaterThan(0);
    });
    it("leaves the camera alone while the bunny walks right", () => {
        // Panning belongs to the input layer's movement module, which is the
        // camera's only writer. Rendering used to pan it too and the speeds added.
        const bunnyState = createTestBunnyState({ kind: "walk", frameIdx: 0 }, true);
        const sceneState = createTestSceneState();
        const initialCameraX = sceneState.camera.x;
        const renderState = {
            bunnyState,
            sceneState,
            viewport: { width: 80, height: 24, charW: 10, charH: 20 },
            lastTime: 1000,
            projectionConfig,
        };
        renderFrame(renderState, createTestBunnyFrames(), screen, 2000);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("leaves the camera alone while the bunny walks left", () => {
        const bunnyState = createTestBunnyState({ kind: "walk", frameIdx: 0 }, false);
        const sceneState = createTestSceneState();
        const initialCameraX = sceneState.camera.x;
        const renderState = {
            bunnyState,
            sceneState,
            viewport: { width: 80, height: 24, charW: 10, charH: 20 },
            lastTime: 1000,
            projectionConfig,
        };
        renderFrame(renderState, createTestBunnyFrames(), screen, 2000);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("handles first frame with zero lastTime", () => {
        const bunnyState = createInitialBunnyState();
        const sceneState = createTestSceneState();
        const renderState = {
            bunnyState,
            sceneState,
            viewport: { width: 80, height: 24, charW: 10, charH: 20 },
            lastTime: 0,
            projectionConfig,
        };
        const bunnyFrames = createTestBunnyFrames();
        const result = renderFrame(renderState, bunnyFrames, screen, 1000);
        expect(result.lastTime).toBe(1000);
    });
    it("leaves the camera alone while the bunny is idle", () => {
        const bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        const sceneState = createTestSceneState();
        const initialCameraX = sceneState.camera.x;
        const renderState = {
            bunnyState,
            sceneState,
            viewport: { width: 80, height: 24, charW: 10, charH: 20 },
            lastTime: 1000,
            projectionConfig,
        };
        const bunnyFrames = createTestBunnyFrames();
        renderFrame(renderState, bunnyFrames, screen, 2000);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("leaves the camera alone while the bunny is jumping", () => {
        const bunnyState = createTestBunnyState({ kind: "jump", frameIdx: 0 });
        const sceneState = createTestSceneState();
        const initialCameraX = sceneState.camera.x;
        const renderState = {
            bunnyState,
            sceneState,
            viewport: { width: 80, height: 24, charW: 10, charH: 20 },
            lastTime: 1000,
            projectionConfig,
        };
        const bunnyFrames = createTestBunnyFrames();
        renderFrame(renderState, bunnyFrames, screen, 2000);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("leaves the camera alone during a transition", () => {
        const bunnyState = createTestBunnyState({ kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" });
        const sceneState = createTestSceneState();
        const initialCameraX = sceneState.camera.x;
        const renderState = {
            bunnyState,
            sceneState,
            viewport: { width: 80, height: 24, charW: 10, charH: 20 },
            lastTime: 1000,
            projectionConfig,
        };
        const bunnyFrames = createTestBunnyFrames();
        renderFrame(renderState, bunnyFrames, screen, 2000);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("renders with scene layers", () => {
        const bunnyState = createInitialBunnyState();
        const sceneState = createTestSceneState();
        const renderState = {
            bunnyState,
            sceneState,
            viewport: { width: 80, height: 24, charW: 10, charH: 20 },
            lastTime: 0,
            projectionConfig,
        };
        const bunnyFrames = createTestBunnyFrames();
        const result = renderFrame(renderState, bunnyFrames, screen, 1000);
        expect(result.lastTime).toBe(1000);
        expect(screen.textContent).not.toBe("");
        expect(screen.textContent.length).toBeGreaterThan(0);
    });
});
describe("drawBunny", () => {
    function createBuffer(width, height) {
        return Array.from({ length: height }, () => Array.from({ length: width }, () => " "));
    }
    it("draws bunny to buffer", () => {
        const buffer = createBuffer(80, 24);
        const bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 }, true);
        const bunnyFrames = createTestBunnyFrames();
        drawBunny(buffer, bunnyState, bunnyFrames, createCamera(), 80, 24, createProjectionConfig());
        // Check that bunny was drawn (has non-space content)
        const hasContent = buffer.some((row) => row.some((char) => char !== " "));
        expect(hasContent).toBe(true);
    });
    it("draws bunny facing left", () => {
        const buffer = createBuffer(80, 24);
        const bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 }, false);
        const bunnyFrames = createTestBunnyFrames();
        drawBunny(buffer, bunnyState, bunnyFrames, createCamera(), 80, 24, createProjectionConfig());
        const hasContent = buffer.some((row) => row.some((char) => char !== " "));
        expect(hasContent).toBe(true);
    });
});
describe("bunny depth occlusion", () => {
    const projectionConfig = createProjectionConfig();
    const VIEWPORT = { width: 120, height: 40, charW: 10, charH: 20 };
    /** Read from the source, never mirrored: copied values here would silently
        stop testing the real placement the moment BUNNY_LAYER moved. */
    const CAMERA = createCamera();
    const BUNNY_WORLD_Z = bunnyWorldZ(CAMERA);
    /** Closest depth projection will draw. Anything nearer is clipped, so a
        "near" tree chosen below this would never render and the occlusion test
        would pass vacuously. */
    const NEAREST_VISIBLE_Z = CAMERA.z + projectionConfig.nearZ;
    /** A tree wide and tall enough to cover the bunny wherever he is drawn. */
    function createCoveringTree(worldZ) {
        const row = "T".repeat(VIEWPORT.width);
        const art = Array.from({ length: VIEWPORT.height }, () => row).join("\n");
        return createTestEntity(0, worldZ, createTestSizes(art, VIEWPORT.width));
    }
    function renderWithTreeAt(worldZ) {
        const screen = document.createElement("pre");
        document.body.appendChild(screen);
        const tree = createCoveringTree(worldZ);
        const layer = createTestLayer("trees", 0, 12, [tree]);
        const state = {
            bunnyState: createInitialBunnyState(),
            sceneState: createSceneState([layer], createCamera(), createTestDepthBounds()),
            viewport: VIEWPORT,
            lastTime: 0,
            projectionConfig,
        };
        renderFrame(state, createTestBunnyFrames(), screen, 16);
        const text = screen.textContent;
        document.body.removeChild(screen);
        return text;
    }
    it("lets a tree nearer than the bunny draw over him", () => {
        // Midway between the clip plane and the bunny: nearer than him, still drawn.
        const nearZ = (NEAREST_VISIBLE_Z + BUNNY_WORLD_Z) / 2;
        expect(nearZ).toBeLessThan(BUNNY_WORLD_Z);
        expect(nearZ).toBeGreaterThanOrEqual(NEAREST_VISIBLE_Z);
        const text = renderWithTreeAt(nearZ);
        expect(text).toContain("T");
        expect(text).not.toContain("idle_l_0");
    });
    it("keeps the bunny visible in front of a tree further away than him", () => {
        const farZ = BUNNY_WORLD_Z + 40;
        expect(farZ).toBeGreaterThan(BUNNY_WORLD_Z);
        const text = renderWithTreeAt(farZ);
        expect(text).toContain("T");
        expect(text).toContain("idle_l_0");
    });
});
describe("drawBunny placement invariant", () => {
    it("throws a traceable error when the bunny projects outside the visible band", () => {
        const buffer = Array.from({ length: 24 }, () => Array(80).fill(" "));
        const bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 }, true);
        const camera = createCamera();
        // Pull the far plane inside the bunny's own distance from the camera, so
        // he becomes unplaceable. Derived, so it holds at any BUNNY_LAYER.
        const distance = bunnyWorldZ(camera) - camera.z;
        const config = { ...createProjectionConfig(), farZ: distance - 1 };
        expect(() => {
            drawBunny(buffer, bunnyState, createTestBunnyFrames(), camera, 80, 24, config);
        }).toThrowError(/BUNNY_UNPLACEABLE/);
    });
});
//# sourceMappingURL=SceneRenderer.test.js.map