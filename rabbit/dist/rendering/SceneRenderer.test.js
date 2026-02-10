/**
 * @vitest-environment jsdom
 * Tests for scene renderer.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderFrame, _test_hooks } from "./SceneRenderer.js";
const { drawBunny } = _test_hooks;
import { createInitialBunnyState } from "../entities/Bunny.js";
import { createSceneState } from "../layers/index.js";
import { createCamera, createProjectionConfig } from "../world/Projection.js";
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
    };
}
function createTestSceneState() {
    return createSceneState([], createCamera());
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
        const result = renderFrame(renderState, bunnyFrames, screen, 1000, 100);
        expect(result.lastTime).toBe(1000);
        expect(screen.textContent).not.toBe("");
        expect(screen.textContent.length).toBeGreaterThan(0);
    });
    it("updates camera when bunny is walking right", () => {
        const bunnyState = createInitialBunnyState();
        bunnyState.isWalking = true;
        bunnyState.currentAnimation = "walk";
        bunnyState.facingRight = true;
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
        renderFrame(renderState, bunnyFrames, screen, 2000, 100);
        expect(sceneState.camera.x).toBeGreaterThan(initialCameraX);
    });
    it("updates camera when bunny walks left", () => {
        const bunnyState = createInitialBunnyState();
        bunnyState.isWalking = true;
        bunnyState.currentAnimation = "walk";
        bunnyState.facingRight = false;
        const sceneState = createTestSceneState();
        const renderState = {
            bunnyState,
            sceneState,
            viewport: { width: 80, height: 24, charW: 10, charH: 20 },
            lastTime: 1000,
            projectionConfig,
        };
        const bunnyFrames = createTestBunnyFrames();
        const initialCameraX = sceneState.camera.x;
        renderFrame(renderState, bunnyFrames, screen, 2000, 100);
        expect(sceneState.camera.x).toBeLessThan(initialCameraX);
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
        const result = renderFrame(renderState, bunnyFrames, screen, 1000, 100);
        expect(result.lastTime).toBe(1000);
    });
    it("does not update camera when bunny is idle", () => {
        const bunnyState = createInitialBunnyState();
        bunnyState.isWalking = false;
        bunnyState.currentAnimation = "idle";
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
        renderFrame(renderState, bunnyFrames, screen, 2000, 100);
        expect(sceneState.camera.x).toBe(initialCameraX);
    });
    it("does not update camera when walking but not in walk animation", () => {
        const bunnyState = createInitialBunnyState();
        bunnyState.isWalking = true;
        bunnyState.currentAnimation = "idle"; // Walking flag set but not in walk animation
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
        renderFrame(renderState, bunnyFrames, screen, 2000, 100);
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
        const result = renderFrame(renderState, bunnyFrames, screen, 1000, 100);
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
        const bunnyState = createInitialBunnyState();
        bunnyState.facingRight = true;
        const bunnyFrames = createTestBunnyFrames();
        drawBunny(buffer, bunnyState, bunnyFrames, 80, 24);
        // Check that bunny was drawn (has non-space content)
        const hasContent = buffer.some((row) => row.some((char) => char !== " "));
        expect(hasContent).toBe(true);
    });
    it("draws bunny facing left", () => {
        const buffer = createBuffer(80, 24);
        const bunnyState = createInitialBunnyState();
        bunnyState.facingRight = false;
        const bunnyFrames = createTestBunnyFrames();
        drawBunny(buffer, bunnyState, bunnyFrames, 80, 24);
        const hasContent = buffer.some((row) => row.some((char) => char !== " "));
        expect(hasContent).toBe(true);
    });
});
//# sourceMappingURL=SceneRenderer.test.js.map