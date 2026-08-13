/**
 * Tests for camera movement driven by effective intent.
 */
import { describe, it, expect } from "vitest";
import { _test_hooks } from "./movement.js";
import { createIntent } from "./intent.js";
import { DEFAULT_CAMERA_Z } from "../world/Projection.js";
import { createTestBunnyState, createTestInputState } from "../testing/fixtures.js";
const { processDepthMovement, processHorizontalMovement, resetCamera, CAMERA_Z_SPEED, CAMERA_X_SPEED } = _test_hooks;
/**
 * Build input state in a given animation with a given intent.
 *
 * Args:
 *     animation: Animation the bunny is in.
 *     horizontal: Horizontal intent in effect.
 *
 * Returns:
 *     InputState ready for a movement call.
 */
function stateIn(animation, horizontal = null) {
    const state = createTestInputState(createTestBunnyState(animation));
    state.intent = createIntent(horizontal, null);
    return state;
}
describe("processDepthMovement", () => {
    it("leaves the camera alone when not hopping", () => {
        const state = stateIn({ kind: "walk", frameIdx: 0 });
        processDepthMovement(state, 1);
        expect(state.camera.z).toBe(0);
    });
    it("moves into the scene when hopping away", () => {
        const state = stateIn({ kind: "hop", direction: "away", frameIdx: 0 });
        processDepthMovement(state, 1);
        expect(state.camera.z).toBe(CAMERA_Z_SPEED);
    });
    it("moves toward the viewer when hopping toward", () => {
        const state = stateIn({ kind: "hop", direction: "toward", frameIdx: 0 });
        processDepthMovement(state, 1);
        expect(state.camera.z).toBe(-CAMERA_Z_SPEED);
    });
    it("scales movement by the frame delta", () => {
        const state = stateIn({ kind: "hop", direction: "away", frameIdx: 0 });
        processDepthMovement(state, 0.5);
        expect(state.camera.z).toBe(CAMERA_Z_SPEED * 0.5);
    });
    it("wraps depth at the far bound instead of running off", () => {
        const state = stateIn({ kind: "hop", direction: "away", frameIdx: 0 });
        state.camera = { x: 0, z: state.depthBounds.maxZ };
        processDepthMovement(state, 1);
        expect(state.camera.z).toBeLessThan(state.depthBounds.maxZ);
        expect(state.camera.z).toBeGreaterThanOrEqual(state.depthBounds.minZ);
    });
    it("preserves the horizontal camera position", () => {
        const state = stateIn({ kind: "hop", direction: "away", frameIdx: 0 });
        state.camera = { x: 42, z: 0 };
        processDepthMovement(state, 1);
        expect(state.camera.x).toBe(42);
    });
});
describe("processHorizontalMovement", () => {
    it("leaves the camera alone when idle", () => {
        const state = stateIn({ kind: "idle", frameIdx: 0 }, "right");
        processHorizontalMovement(state, 1);
        expect(state.camera.x).toBe(0);
    });
    it("leaves the camera alone when walking without intent", () => {
        const state = stateIn({ kind: "walk", frameIdx: 0 }, null);
        processHorizontalMovement(state, 1);
        expect(state.camera.x).toBe(0);
    });
    it("scrolls right while walking right", () => {
        const state = stateIn({ kind: "walk", frameIdx: 0 }, "right");
        processHorizontalMovement(state, 1);
        expect(state.camera.x).toBe(CAMERA_X_SPEED);
    });
    it("scrolls left while walking left", () => {
        const state = stateIn({ kind: "walk", frameIdx: 0 }, "left");
        processHorizontalMovement(state, 1);
        expect(state.camera.x).toBe(-CAMERA_X_SPEED);
    });
    it("scrolls while hopping", () => {
        const state = stateIn({ kind: "hop", direction: "away", frameIdx: 0 }, "right");
        processHorizontalMovement(state, 1);
        expect(state.camera.x).toBe(CAMERA_X_SPEED);
    });
    it("scrolls while jumping", () => {
        const state = stateIn({ kind: "jump", frameIdx: 0 }, "right");
        processHorizontalMovement(state, 1);
        expect(state.camera.x).toBe(CAMERA_X_SPEED);
    });
    it("does not scroll during a transition", () => {
        const state = stateIn({ kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" }, "right");
        processHorizontalMovement(state, 1);
        expect(state.camera.x).toBe(0);
    });
    it("preserves the depth camera position", () => {
        const state = stateIn({ kind: "walk", frameIdx: 0 }, "right");
        state.camera = { x: 0, z: 17 };
        processHorizontalMovement(state, 1);
        expect(state.camera.z).toBe(17);
    });
});
describe("resetCamera", () => {
    it("returns the camera to the origin at the default depth", () => {
        const state = stateIn({ kind: "walk", frameIdx: 0 }, "right");
        state.camera = { x: 500, z: 90 };
        resetCamera(state);
        expect(state.camera).toStrictEqual({ x: 0, z: DEFAULT_CAMERA_Z });
    });
});
//# sourceMappingURL=movement.test.js.map