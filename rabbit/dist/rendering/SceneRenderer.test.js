/**
 * @vitest-environment jsdom
 * Tests for scene renderer.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderFrame, applyLayerColors, _test_hooks, } from "./SceneRenderer.js";
const { drawBunny } = _test_hooks;
import { createInitialBunnyState } from "../entities/Bunny.js";
import { createSceneState } from "../layers/index.js";
import { createCamera, createProjectionConfig } from "../world/Projection.js";
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
    let layers;
    const projectionConfig = createProjectionConfig();
    beforeEach(() => {
        const world = document.createElement("pre");
        const actor = document.createElement("pre");
        const foreground = document.createElement("pre");
        document.body.append(world, actor, foreground);
        layers = { world, actor, foreground };
    });
    afterEach(() => {
        document.body.replaceChildren();
    });
    function createRenderState(bunnyState, sceneState, lastTime = 0) {
        return {
            bunnyState,
            sceneState,
            viewport: { width: 80, height: 24, charW: 10, charH: 20 },
            lastTime,
            projectionConfig,
        };
    }
    it("renders frame and returns updated state", () => {
        const renderState = createRenderState(createInitialBunnyState(), createTestSceneState());
        const result = renderFrame(renderState, createTestBunnyFrames(), layers, 1000);
        expect(result.lastTime).toBe(1000);
        expect(layers.world.textContent).not.toBe("");
        expect(layers.world.textContent.length).toBeGreaterThan(0);
    });
    it("writes every layer, not just the world", () => {
        const renderState = createRenderState(createInitialBunnyState(), createTestSceneState());
        renderFrame(renderState, createTestBunnyFrames(), layers, 1000);
        expect(layers.world.textContent.length).toBeGreaterThan(0);
        expect(layers.actor.textContent.length).toBeGreaterThan(0);
        expect(layers.foreground.textContent.length).toBeGreaterThan(0);
    });
    it("gives all three layers identical grid dimensions", () => {
        // The layers are stacked with no positioning arithmetic, so they only stay
        // aligned while every one of them is the full viewport grid. A layer that
        // trimmed its trailing spaces would drift out of registration.
        const renderState = createRenderState(createInitialBunnyState(), createTestSceneState());
        renderFrame(renderState, createTestBunnyFrames(), layers, 1000);
        const rows = [layers.world, layers.actor, layers.foreground].map((el) => el.textContent.split("\n"));
        for (const grid of rows) {
            expect(grid).toHaveLength(24);
            for (const row of grid) {
                expect(row).toHaveLength(80);
            }
        }
    });
    it("draws the bunny onto the actor layer and nowhere else", () => {
        const renderState = createRenderState(createTestBunnyState({ kind: "idle", frameIdx: 0 }), createTestSceneState());
        renderFrame(renderState, createTestBunnyFrames(), layers, 1000);
        expect(layers.actor.textContent).toContain("idle_l_0");
        expect(layers.world.textContent).not.toContain("idle_l_0");
        expect(layers.foreground.textContent).not.toContain("idle_l_0");
    });
    it("leaves the foreground layer empty when no foreground layers exist", () => {
        // Occlusion depends on unwritten cells staying spaces: a foreground layer
        // that painted anything opaque would hide the actor everywhere.
        const renderState = createRenderState(createInitialBunnyState(), createTestSceneState());
        renderFrame(renderState, createTestBunnyFrames(), layers, 1000);
        expect(layers.foreground.textContent.trim()).toBe("");
    });
    it("draws the ground onto the world layer, not the actor layer", () => {
        const renderState = createRenderState(createInitialBunnyState(), createTestSceneState());
        renderFrame(renderState, createTestBunnyFrames(), layers, 1000);
        // The actor layer holds the bunny frame and nothing else, so removing the
        // frame's own glyphs must leave it blank.
        const actorWithoutBunny = layers.actor.textContent.replace(/idle_l_0/g, "");
        expect(actorWithoutBunny.trim()).toBe("");
        expect(layers.world.textContent.trim()).not.toBe("");
    });
    it("leaves the camera alone while the bunny walks right", () => {
        // Panning belongs to the input layer's movement module, which is the
        // camera's only writer. Rendering used to pan it too and the speeds added.
        const sceneState = createTestSceneState();
        const initialCameraX = sceneState.camera.x;
        const renderState = createRenderState(createTestBunnyState({ kind: "walk", frameIdx: 0 }, true), sceneState, 1000);
        renderFrame(renderState, createTestBunnyFrames(), layers, 2000);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("leaves the camera alone while the bunny walks left", () => {
        const sceneState = createTestSceneState();
        const initialCameraX = sceneState.camera.x;
        const renderState = createRenderState(createTestBunnyState({ kind: "walk", frameIdx: 0 }, false), sceneState, 1000);
        renderFrame(renderState, createTestBunnyFrames(), layers, 2000);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("handles first frame with zero lastTime", () => {
        const renderState = createRenderState(createInitialBunnyState(), createTestSceneState());
        const result = renderFrame(renderState, createTestBunnyFrames(), layers, 1000);
        expect(result.lastTime).toBe(1000);
    });
    it("leaves the camera alone while the bunny is idle", () => {
        const sceneState = createTestSceneState();
        const initialCameraX = sceneState.camera.x;
        const renderState = createRenderState(createTestBunnyState({ kind: "idle", frameIdx: 0 }), sceneState, 1000);
        renderFrame(renderState, createTestBunnyFrames(), layers, 2000);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("leaves the camera alone while the bunny is jumping", () => {
        const sceneState = createTestSceneState();
        const initialCameraX = sceneState.camera.x;
        const renderState = createRenderState(createTestBunnyState({ kind: "jump", frameIdx: 0 }), sceneState, 1000);
        renderFrame(renderState, createTestBunnyFrames(), layers, 2000);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("leaves the camera alone during a transition", () => {
        const sceneState = createTestSceneState();
        const initialCameraX = sceneState.camera.x;
        const renderState = createRenderState(createTestBunnyState({
            kind: "transition",
            type: "walk_to_idle",
            frameIdx: 0,
            pendingAction: null,
            returnTo: "idle",
        }), sceneState, 1000);
        renderFrame(renderState, createTestBunnyFrames(), layers, 2000);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("renders with scene layers", () => {
        const renderState = createRenderState(createInitialBunnyState(), createTestSceneState());
        const result = renderFrame(renderState, createTestBunnyFrames(), layers, 1000);
        expect(result.lastTime).toBe(1000);
        expect(layers.world.textContent).not.toBe("");
        expect(layers.world.textContent.length).toBeGreaterThan(0);
    });
});
describe("applyLayerColors", () => {
    it("sets each layer's colour independently", () => {
        const world = document.createElement("pre");
        const actor = document.createElement("pre");
        const foreground = document.createElement("pre");
        applyLayerColors({ world, actor, foreground }, { world: "#111111", actor: "#6db3ff", foreground: "#222222" });
        expect(world.style.color).toBe("rgb(17, 17, 17)");
        expect(actor.style.color).toBe("rgb(109, 179, 255)");
        expect(foreground.style.color).toBe("rgb(34, 34, 34)");
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
        drawBunny(buffer, bunnyState, bunnyFrames, 80, 24);
        // Check that bunny was drawn (has non-space content)
        const hasContent = buffer.some((row) => row.some((char) => char !== " "));
        expect(hasContent).toBe(true);
    });
    it("draws bunny facing left", () => {
        const buffer = createBuffer(80, 24);
        const bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 }, false);
        const bunnyFrames = createTestBunnyFrames();
        drawBunny(buffer, bunnyState, bunnyFrames, 80, 24);
        const hasContent = buffer.some((row) => row.some((char) => char !== " "));
        expect(hasContent).toBe(true);
    });
});
//# sourceMappingURL=SceneRenderer.test.js.map