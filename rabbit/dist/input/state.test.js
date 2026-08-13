/**
 * Tests for input state construction and intent inspection.
 */
import { describe, it, expect } from "vitest";
import { _test_hooks } from "./state.js";
import { createIntent } from "./intent.js";
import { createTestBunnyState, createTestDepthBounds } from "../testing/fixtures.js";
const { createInputState, isHorizontalRequested, createHorizontalHeldProbe } = _test_hooks;
describe("createInputState", () => {
    it("starts with a neutral intent", () => {
        const state = createInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }), { width: 80, height: 24, charW: 8, charH: 16 }, { x: 5, z: 12 }, createTestDepthBounds());
        expect(state.intent.horizontal).toBeNull();
        expect(state.intent.vertical).toBeNull();
    });
    it("retains the supplied camera and viewport", () => {
        const bounds = createTestDepthBounds();
        const state = createInputState(createTestBunnyState({ kind: "walk", frameIdx: 1 }, true), { width: 80, height: 24, charW: 8, charH: 16 }, { x: 5, z: 12 }, bounds);
        expect(state.camera).toStrictEqual({ x: 5, z: 12 });
        expect(state.viewport.width).toBe(80);
        expect(state.depthBounds).toStrictEqual(bounds);
        expect(state.bunny.facingRight).toBe(true);
    });
});
describe("isHorizontalRequested", () => {
    it("is false for a neutral intent", () => {
        const state = createTestStateWithIntent(null);
        expect(isHorizontalRequested(state)).toBe(false);
    });
    it("is true when walking left", () => {
        const state = createTestStateWithIntent("left");
        expect(isHorizontalRequested(state)).toBe(true);
    });
    it("is true when walking right", () => {
        const state = createTestStateWithIntent("right");
        expect(isHorizontalRequested(state)).toBe(true);
    });
});
describe("createHorizontalHeldProbe", () => {
    it("reports the intent in effect at the moment it is called", () => {
        const state = createTestStateWithIntent(null);
        const probe = createHorizontalHeldProbe(state);
        expect(probe()).toBe(false);
        state.intent = createIntent("right", null);
        expect(probe()).toBe(true);
        state.intent = createIntent(null, "up");
        expect(probe()).toBe(false);
    });
});
/**
 * Build input state carrying a specific horizontal intent.
 *
 * Args:
 *     horizontal: Horizontal intent to apply.
 *
 * Returns:
 *     InputState with that intent in effect.
 */
function createTestStateWithIntent(horizontal) {
    const state = createInputState(createTestBunnyState({ kind: "idle", frameIdx: 0 }), { width: 80, height: 24, charW: 8, charH: 16 }, { x: 0, z: 0 }, createTestDepthBounds());
    state.intent = createIntent(horizontal, null);
    return state;
}
//# sourceMappingURL=state.test.js.map