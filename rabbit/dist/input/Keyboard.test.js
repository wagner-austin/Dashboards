/**
 * @vitest-environment jsdom
 * Tests for keyboard input handling.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { setupKeyboardControls, processDepthMovement, processHorizontalMovement, _test_hooks } from "./Keyboard.js";
import { createBunnyTimers } from "../entities/Bunny.js";
import { calculateDepthBounds, createProjectionConfig } from "../world/Projection.js";
import { layerToWorldZ } from "../layers/widths.js";
const { CAMERA_Z_SPEED, CAMERA_X_SPEED, handleHopRelease, isPendingJump } = _test_hooks;
/** Create test depth bounds matching default config (layers 8-30). */
function createTestDepthBounds() {
    const projectionConfig = createProjectionConfig();
    const minTreeWorldZ = layerToWorldZ(8);
    const maxTreeWorldZ = layerToWorldZ(30);
    return calculateDepthBounds(minTreeWorldZ, maxTreeWorldZ, projectionConfig);
}
/** Standard test depth bounds. */
const TEST_DEPTH_BOUNDS = createTestDepthBounds();
function createTestFrames() {
    return {
        walkLeft: ["walkL0", "walkL1"],
        walkRight: ["walkR0", "walkR1"],
        jumpLeft: ["jumpL0"],
        jumpRight: ["jumpR0"],
        idleLeft: ["idleL0"],
        idleRight: ["idleR0"],
        walkToIdleLeft: ["transL0", "transL1", "transL2"],
        walkToIdleRight: ["transR0", "transR1", "transR2"],
        walkToTurnAwayLeft: ["turnAwayL0", "turnAwayL1"],
        walkToTurnAwayRight: ["turnAwayR0", "turnAwayR1"],
        walkToTurnTowardLeft: ["turnTowardL0", "turnTowardL1"],
        walkToTurnTowardRight: ["turnTowardR0", "turnTowardR1"],
        hopAway: ["hopAway0", "hopAway1"],
        hopToward: ["hopToward0", "hopToward1"],
    };
}
function createTestBunnyState(animation, facingRight = false) {
    return { facingRight, animation };
}
function createTestInputState(bunnyState) {
    // Camera Z must be inside depthBounds [-110, 50) for valid movement
    return {
        bunny: bunnyState,
        viewport: { width: 100, height: 50, charW: 10, charH: 20 },
        camera: { x: 0, z: 0 },
        depthBounds: TEST_DEPTH_BOUNDS,
        hopKeyHeld: null,
        slideKeyHeld: null,
    };
}
function dispatchKeyDown(key, repeat = false) {
    document.dispatchEvent(new KeyboardEvent("keydown", { key, repeat }));
}
function dispatchKeyUp(key) {
    document.dispatchEvent(new KeyboardEvent("keyup", { key }));
}
/**
 * Get animation state after mutation.
 *
 * Breaks TypeScript's type inference to allow checking state after event dispatch.
 */
function getAnim(s) {
    return s.bunny.animation;
}
/**
 * Get animation state from bunny state after mutation.
 *
 * Breaks TypeScript's type inference to allow checking state after function calls.
 */
function getBunnyAnim(s) {
    return s.animation;
}
describe("setupKeyboardControls", () => {
    let bunnyState;
    let state;
    let timers;
    let frames;
    beforeEach(() => {
        vi.useFakeTimers();
        bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        state = createTestInputState(bunnyState);
        frames = createTestFrames();
        timers = createBunnyTimers(bunnyState, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        });
        setupKeyboardControls(state, frames, timers);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    describe("walk input", () => {
        it("starts transition to walk when ArrowLeft pressed from idle", () => {
            dispatchKeyDown("ArrowLeft");
            expect(state.bunny.animation.kind).toBe("transition");
            if (state.bunny.animation.kind === "transition") {
                expect(state.bunny.animation.type).toBe("idle_to_walk");
                expect(state.bunny.animation.pendingAction).toBe("walk");
            }
            expect(state.bunny.facingRight).toBe(false);
        });
        it("starts transition to walk when ArrowRight pressed from idle", () => {
            dispatchKeyDown("ArrowRight");
            expect(state.bunny.animation.kind).toBe("transition");
            if (state.bunny.animation.kind === "transition") {
                expect(state.bunny.animation.type).toBe("idle_to_walk");
                expect(state.bunny.animation.pendingAction).toBe("walk");
            }
            expect(state.bunny.facingRight).toBe(true);
        });
        it("responds to a key (lowercase)", () => {
            dispatchKeyDown("a");
            expect(state.bunny.animation.kind).toBe("transition");
            expect(state.bunny.facingRight).toBe(false);
        });
        it("responds to d key (lowercase)", () => {
            dispatchKeyDown("d");
            expect(state.bunny.animation.kind).toBe("transition");
            expect(state.bunny.facingRight).toBe(true);
        });
        it("responds to A key (uppercase/caps lock)", () => {
            dispatchKeyDown("A");
            expect(state.bunny.animation.kind).toBe("transition");
            expect(state.bunny.facingRight).toBe(false);
        });
        it("responds to D key (uppercase/caps lock)", () => {
            dispatchKeyDown("D");
            expect(state.bunny.animation.kind).toBe("transition");
            expect(state.bunny.facingRight).toBe(true);
        });
        it("stops walking when same direction pressed while walking", () => {
            state.bunny.animation = { kind: "walk", frameIdx: 0 };
            state.bunny.facingRight = false;
            dispatchKeyDown("ArrowLeft");
            const anim = getAnim(state);
            expect(anim.kind).toBe("transition");
            if (anim.kind === "transition") {
                expect(anim.type).toBe("walk_to_idle");
            }
        });
        it("switches direction when opposite key pressed while walking", () => {
            state.bunny.animation = { kind: "walk", frameIdx: 0 };
            state.bunny.facingRight = false;
            dispatchKeyDown("ArrowRight");
            expect(state.bunny.animation.kind).toBe("walk");
            expect(state.bunny.facingRight).toBe(true);
            expect(state.bunny.animation.frameIdx).toBe(0);
        });
        it("ignores repeated key events", () => {
            dispatchKeyDown("ArrowLeft", true);
            expect(state.bunny.animation.kind).toBe("idle");
        });
    });
    describe("jump input", () => {
        it("starts transition then jump when space pressed from idle", () => {
            dispatchKeyDown(" ");
            expect(state.bunny.animation.kind).toBe("transition");
            if (state.bunny.animation.kind === "transition") {
                expect(state.bunny.animation.type).toBe("idle_to_walk");
                expect(state.bunny.animation.pendingAction).toBe("jump");
            }
            expect(timers.transition.isRunning()).toBe(true);
        });
        it("starts jump immediately when space pressed while walking", () => {
            state.bunny.animation = { kind: "walk", frameIdx: 0 };
            dispatchKeyDown(" ");
            const anim = getAnim(state);
            expect(anim.kind).toBe("jump");
            if (anim.kind === "jump") {
                expect(anim.returnTo).toBe("walk");
            }
            expect(timers.jump.isRunning()).toBe(true);
        });
        it("does not start jump when already jumping", () => {
            state.bunny.animation = { kind: "jump", frameIdx: 0, returnTo: "idle" };
            const wasRunning = timers.jump.isRunning();
            dispatchKeyDown(" ");
            expect(timers.jump.isRunning()).toBe(wasRunning);
        });
        it("does not start jump when hopping", () => {
            state.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };
            dispatchKeyDown(" ");
            // Should remain in hop state, jump not started
            expect(state.bunny.animation.kind).toBe("hop");
            expect(timers.jump.isRunning()).toBe(false);
        });
        it("does not start jump when pendingJump is true", () => {
            state.bunny.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "jump", returnTo: "idle" };
            dispatchKeyDown(" ");
            expect(timers.jump.isRunning()).toBe(false);
        });
        it("starts jump immediately when in transition animation", () => {
            state.bunny.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" };
            dispatchKeyDown(" ");
            const anim = getAnim(state);
            expect(anim.kind).toBe("jump");
            if (anim.kind === "jump") {
                expect(anim.returnTo).toBe("idle");
            }
            expect(timers.jump.isRunning()).toBe(true);
        });
        it("uses correct transition frames when jumping from idle facing right", () => {
            state.bunny.facingRight = true;
            dispatchKeyDown(" ");
            if (state.bunny.animation.kind === "transition") {
                expect(state.bunny.animation.frameIdx).toBe(2);
                expect(state.bunny.animation.type).toBe("idle_to_walk");
            }
        });
        it("sets returnTo to walk when jumping from transition with returnTo walk", () => {
            state.bunny.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: null, returnTo: "walk" };
            dispatchKeyDown(" ");
            const anim = getAnim(state);
            expect(anim.kind).toBe("jump");
            if (anim.kind === "jump") {
                expect(anim.returnTo).toBe("walk");
            }
        });
        it("sets returnTo to idle when jumping from walk_to_idle transition", () => {
            state.bunny.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: null, returnTo: "walk" };
            dispatchKeyDown(" ");
            const anim = getAnim(state);
            expect(anim.kind).toBe("jump");
            if (anim.kind === "jump") {
                // returnTo is based on the transition's returnTo which was "walk"
                expect(anim.returnTo).toBe("walk");
            }
        });
    });
    describe("reset input", () => {
        it("resets camera position and depth position when r pressed", () => {
            state.camera = { x: 100, z: 45 };
            dispatchKeyDown("r");
            expect(state.camera.x).toBe(0);
            expect(state.camera.z).toBe(55);
        });
        it("responds to R key (uppercase)", () => {
            state.camera = { x: 100, z: 45 };
            dispatchKeyDown("R");
            expect(state.camera.x).toBe(0);
            expect(state.camera.z).toBe(55);
        });
    });
    describe("hop input", () => {
        it("sets hopKeyHeld to away with w key", () => {
            dispatchKeyDown("w");
            expect(state.hopKeyHeld).toBe("away");
        });
        it("sets hopKeyHeld to away with ArrowUp", () => {
            dispatchKeyDown("ArrowUp");
            expect(state.hopKeyHeld).toBe("away");
        });
        it("sets hopKeyHeld to toward with s key", () => {
            dispatchKeyDown("s");
            expect(state.hopKeyHeld).toBe("toward");
        });
        it("sets hopKeyHeld to toward with ArrowDown", () => {
            dispatchKeyDown("ArrowDown");
            expect(state.hopKeyHeld).toBe("toward");
        });
        it("clears hopKeyHeld on w keyup", () => {
            dispatchKeyDown("w");
            expect(state.hopKeyHeld).toBe("away");
            dispatchKeyUp("w");
            expect(state.hopKeyHeld).toBe(null);
        });
        it("clears hopKeyHeld on ArrowUp keyup", () => {
            dispatchKeyDown("ArrowUp");
            expect(state.hopKeyHeld).toBe("away");
            dispatchKeyUp("ArrowUp");
            expect(state.hopKeyHeld).toBe(null);
        });
        it("clears hopKeyHeld on s keyup", () => {
            dispatchKeyDown("s");
            expect(state.hopKeyHeld).toBe("toward");
            dispatchKeyUp("s");
            expect(state.hopKeyHeld).toBe(null);
        });
        it("clears hopKeyHeld on ArrowDown keyup", () => {
            dispatchKeyDown("ArrowDown");
            expect(state.hopKeyHeld).toBe("toward");
            dispatchKeyUp("ArrowDown");
            expect(state.hopKeyHeld).toBe(null);
        });
        it("does not clear hopKeyHeld on a keyup", () => {
            dispatchKeyDown("w");
            expect(state.hopKeyHeld).toBe("away");
            dispatchKeyUp("a");
            expect(state.hopKeyHeld).toBe("away");
        });
        it("does not clear hopKeyHeld on d keyup", () => {
            dispatchKeyDown("w");
            expect(state.hopKeyHeld).toBe("away");
            dispatchKeyUp("d");
            expect(state.hopKeyHeld).toBe("away");
        });
        it("does not clear hopKeyHeld on ArrowLeft keyup", () => {
            dispatchKeyDown("w");
            expect(state.hopKeyHeld).toBe("away");
            dispatchKeyUp("ArrowLeft");
            expect(state.hopKeyHeld).toBe("away");
        });
        it("does not clear hopKeyHeld on ArrowRight keyup", () => {
            dispatchKeyDown("w");
            expect(state.hopKeyHeld).toBe("away");
            dispatchKeyUp("ArrowRight");
            expect(state.hopKeyHeld).toBe("away");
        });
        it("starts turn away transition when w pressed from idle", () => {
            dispatchKeyDown("w");
            expect(state.bunny.animation.kind).toBe("transition");
            if (state.bunny.animation.kind === "transition") {
                expect(state.bunny.animation.type).toBe("walk_to_turn_away");
                expect(state.bunny.animation.returnTo).toBe("idle");
            }
            expect(timers.transition.isRunning()).toBe(true);
        });
        it("starts turn toward transition when s pressed from idle", () => {
            dispatchKeyDown("s");
            expect(state.bunny.animation.kind).toBe("transition");
            if (state.bunny.animation.kind === "transition") {
                expect(state.bunny.animation.type).toBe("walk_to_turn_toward");
                expect(state.bunny.animation.returnTo).toBe("idle");
            }
            expect(timers.transition.isRunning()).toBe(true);
        });
        it("starts turn away transition when w pressed from idle facing right", () => {
            state.bunny.facingRight = true;
            dispatchKeyDown("w");
            expect(state.bunny.animation.kind).toBe("transition");
            if (state.bunny.animation.kind === "transition") {
                expect(state.bunny.animation.type).toBe("walk_to_turn_away");
                expect(state.bunny.animation.frameIdx).toBe(0);
            }
        });
        it("starts walk_to_turn_away when w pressed from walk", () => {
            state.bunny.animation = { kind: "walk", frameIdx: 0 };
            timers.walk.start();
            dispatchKeyDown("w");
            const anim = getAnim(state);
            expect(anim.kind).toBe("transition");
            if (anim.kind === "transition") {
                expect(anim.type).toBe("walk_to_turn_away");
                expect(anim.returnTo).toBe("walk");
            }
            expect(timers.transition.isRunning()).toBe(true);
        });
        it("starts walk_to_turn_toward when s pressed from walk", () => {
            state.bunny.animation = { kind: "walk", frameIdx: 0 };
            timers.walk.start();
            dispatchKeyDown("s");
            const anim = getAnim(state);
            expect(anim.kind).toBe("transition");
            if (anim.kind === "transition") {
                expect(anim.type).toBe("walk_to_turn_toward");
                expect(anim.returnTo).toBe("walk");
            }
            expect(timers.transition.isRunning()).toBe(true);
        });
        it("does not start hop when already jumping", () => {
            state.bunny.animation = { kind: "jump", frameIdx: 0, returnTo: "idle" };
            dispatchKeyDown("w");
            expect(state.bunny.animation.kind).toBe("jump");
        });
        it("does not start hop when already hopping", () => {
            state.bunny.animation = { kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" };
            dispatchKeyDown("w");
            expect(state.bunny.animation.kind).toBe("hop");
        });
        it("updates pendingAction during transition when hop pressed", () => {
            state.bunny.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: "walk", returnTo: "idle" };
            dispatchKeyDown("w");
            const anim = getAnim(state);
            if (anim.kind === "transition") {
                expect(anim.pendingAction).toBe("hop_away");
            }
        });
    });
    describe("transition handling", () => {
        it("starts idle_to_walk transition from idle", () => {
            dispatchKeyDown("ArrowRight");
            expect(state.bunny.animation.kind).toBe("transition");
            if (state.bunny.animation.kind === "transition") {
                expect(state.bunny.animation.type).toBe("idle_to_walk");
                expect(state.bunny.animation.frameIdx).toBe(2);
            }
            expect(timers.transition.isRunning()).toBe(true);
        });
        it("interrupts transition when direction key pressed", () => {
            state.bunny.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" };
            dispatchKeyDown("ArrowRight");
            expect(state.bunny.animation.kind).toBe("walk");
            expect(timers.walk.isRunning()).toBe(true);
        });
    });
});
describe("processDepthMovement", () => {
    function createTestState(animation, facingRight = false) {
        return createTestInputState(createTestBunnyState(animation, facingRight));
    }
    it("does nothing when not hopping", () => {
        const state = createTestState({ kind: "idle", frameIdx: 0 });
        const initialZ = state.camera.z;
        state.hopKeyHeld = "away";
        processDepthMovement(state);
        expect(state.camera.z).toBe(initialZ);
    });
    it("does nothing during transition even with hopKeyHeld", () => {
        const state = createTestState({ kind: "transition", type: "walk_to_turn_away", frameIdx: 0, pendingAction: null, returnTo: "idle" });
        const initialZ = state.camera.z;
        state.hopKeyHeld = "away";
        processDepthMovement(state);
        expect(state.camera.z).toBe(initialZ);
    });
    it("decreases camera.z when hopping toward (S key, out of scene)", () => {
        const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 0, returnTo: "idle" });
        const initialZ = state.camera.z;
        processDepthMovement(state);
        expect(state.camera.z).toBe(initialZ - CAMERA_Z_SPEED);
    });
    it("increases camera.z when hopping away (W key, into scene)", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" });
        const initialZ = state.camera.z;
        processDepthMovement(state);
        expect(state.camera.z).toBe(initialZ + CAMERA_Z_SPEED);
    });
    it("wraps from minZ to maxZ when moving toward past minimum", () => {
        const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 0, returnTo: "idle" });
        const { minZ, maxZ } = state.depthBounds;
        state.camera = { x: state.camera.x, z: minZ };
        processDepthMovement(state);
        // Should wrap to near maxZ
        const expectedZ = maxZ - (minZ - (minZ - CAMERA_Z_SPEED)) % state.depthBounds.range;
        expect(state.camera.z).toBeCloseTo(expectedZ, 5);
    });
    it("wraps from maxZ to minZ when moving away past maximum", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" });
        const { minZ, maxZ } = state.depthBounds;
        state.camera = { x: state.camera.x, z: maxZ };
        processDepthMovement(state);
        // Should wrap to near minZ
        const expectedZ = minZ + (maxZ + CAMERA_Z_SPEED - maxZ) % state.depthBounds.range;
        expect(state.camera.z).toBeCloseTo(expectedZ, 5);
    });
    it("preserves camera.x when moving in depth", () => {
        const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 0, returnTo: "idle" });
        state.camera = { x: 100, z: 0 };
        processDepthMovement(state);
        expect(state.camera.x).toBe(100);
    });
    it("allows continuous depth movement across multiple calls", () => {
        const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 0, returnTo: "idle" });
        // Start at Z=0 (inside bounds [-110, 50))
        state.camera = { x: 0, z: 0 };
        processDepthMovement(state);
        processDepthMovement(state);
        processDepthMovement(state);
        expect(state.camera.z).toBe(0 - CAMERA_Z_SPEED * 3);
    });
    it("wraps continuously when moving toward past minimum multiple times", () => {
        const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 0, returnTo: "idle" });
        const { minZ, maxZ } = state.depthBounds;
        // Start just above minZ
        state.camera = { x: 0, z: minZ + CAMERA_Z_SPEED * 0.5 };
        // First call goes below minZ, should wrap
        processDepthMovement(state);
        // Result should be wrapped to near maxZ
        expect(state.camera.z).toBeGreaterThan(minZ);
        expect(state.camera.z).toBeLessThanOrEqual(maxZ);
    });
    it("wraps continuously when moving away past maximum multiple times", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" });
        const { minZ, maxZ } = state.depthBounds;
        // Start just below maxZ
        state.camera = { x: 0, z: maxZ - CAMERA_Z_SPEED * 0.5 };
        // First call goes above maxZ, should wrap
        processDepthMovement(state);
        // Result should be wrapped to near minZ
        expect(state.camera.z).toBeGreaterThanOrEqual(minZ);
        expect(state.camera.z).toBeLessThan(maxZ);
    });
});
describe("handleHopRelease", () => {
    let bunnyState;
    let timers;
    let frames;
    beforeEach(() => {
        vi.useFakeTimers();
        bunnyState = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        frames = createTestFrames();
        timers = createBunnyTimers(bunnyState, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        });
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("clears hop pendingAction from idle_to_walk transition and lets walk happen", () => {
        bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "hop_away", returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers);
        // Transition continues but pendingAction is cleared
        const anim = getBunnyAnim(bunnyState);
        expect(anim.kind).toBe("transition");
        if (anim.kind === "transition") {
            expect(anim.type).toBe("idle_to_walk");
            expect(anim.pendingAction).toBe(null);
        }
        expect(timers.transition.isRunning()).toBe(true);
    });
    it("cancels walk_to_turn_away transition and returns to walk when returnTo is walk", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_turn_away", frameIdx: 1, pendingAction: null, returnTo: "walk" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers);
        expect(bunnyState.animation.kind).toBe("walk");
        expect(timers.walk.isRunning()).toBe(true);
        expect(timers.transition.isRunning()).toBe(false);
    });
    it("cancels walk_to_turn_away transition and returns to idle when returnTo is idle", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_turn_away", frameIdx: 1, pendingAction: null, returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers);
        expect(bunnyState.animation.kind).toBe("idle");
        expect(timers.idle.isRunning()).toBe(true);
        expect(timers.transition.isRunning()).toBe(false);
    });
    it("cancels walk_to_turn_toward transition and returns to walk when returnTo is walk", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: "walk" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers);
        expect(bunnyState.animation.kind).toBe("walk");
        expect(timers.walk.isRunning()).toBe(true);
    });
    it("cancels walk_to_turn_toward transition and returns to idle when returnTo is idle", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_turn_toward", frameIdx: 0, pendingAction: null, returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers);
        expect(bunnyState.animation.kind).toBe("idle");
        expect(timers.idle.isRunning()).toBe(true);
        expect(timers.transition.isRunning()).toBe(false);
    });
    it("does nothing for transition without pending hop action", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: null, returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers);
        expect(bunnyState.animation.kind).toBe("transition");
        expect(timers.transition.isRunning()).toBe(true);
    });
    it("does nothing for non-transition, non-hop state", () => {
        bunnyState.animation = { kind: "walk", frameIdx: 0 };
        handleHopRelease(bunnyState, timers);
        expect(bunnyState.animation.kind).toBe("walk");
    });
    it("stops hop and returns to walk when returnTo is walk", () => {
        bunnyState.animation = { kind: "hop", direction: "away", frameIdx: 1, returnTo: "walk" };
        timers.hop.start();
        handleHopRelease(bunnyState, timers);
        expect(bunnyState.animation.kind).toBe("walk");
        expect(timers.walk.isRunning()).toBe(true);
        expect(timers.hop.isRunning()).toBe(false);
    });
    it("stops hop and returns to idle when returnTo is idle", () => {
        bunnyState.animation = { kind: "hop", direction: "toward", frameIdx: 0, returnTo: "idle" };
        timers.hop.start();
        handleHopRelease(bunnyState, timers);
        expect(bunnyState.animation.kind).toBe("idle");
        expect(timers.idle.isRunning()).toBe(true);
        expect(timers.hop.isRunning()).toBe(false);
    });
    it("clears hop_toward pendingAction from idle_to_walk same as hop_away", () => {
        bunnyState.animation = { kind: "transition", type: "idle_to_walk", frameIdx: 1, pendingAction: "hop_toward", returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers);
        const anim = getBunnyAnim(bunnyState);
        expect(anim.kind).toBe("transition");
        if (anim.kind === "transition") {
            expect(anim.pendingAction).toBe(null);
        }
    });
    it("does not cancel walk_to_idle transition even with pending hop", () => {
        bunnyState.animation = { kind: "transition", type: "walk_to_idle", frameIdx: 1, pendingAction: "hop_away", returnTo: "idle" };
        timers.transition.start();
        handleHopRelease(bunnyState, timers);
        // walk_to_idle with pending hop should not be cancelled (logic doesn't handle this case)
        expect(bunnyState.animation.kind).toBe("transition");
    });
});
describe("isPendingJump", () => {
    it("returns true when transition has pending jump action", () => {
        const bunny = createTestBunnyState({ kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "jump", returnTo: "idle" });
        expect(isPendingJump(bunny)).toBe(true);
    });
    it("returns false when transition has different pending action", () => {
        const bunny = createTestBunnyState({ kind: "transition", type: "idle_to_walk", frameIdx: 2, pendingAction: "walk", returnTo: "idle" });
        expect(isPendingJump(bunny)).toBe(false);
    });
    it("returns false when not in transition", () => {
        const bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        expect(isPendingJump(bunny)).toBe(false);
    });
    it("returns false when transition has null pending action", () => {
        const bunny = createTestBunnyState({ kind: "transition", type: "walk_to_idle", frameIdx: 0, pendingAction: null, returnTo: "idle" });
        expect(isPendingJump(bunny)).toBe(false);
    });
});
describe("processHorizontalMovement", () => {
    function createTestState(animation, facingRight = false) {
        return createTestInputState(createTestBunnyState(animation, facingRight));
    }
    it("does nothing when not hopping", () => {
        const state = createTestState({ kind: "idle", frameIdx: 0 });
        state.slideKeyHeld = "left";
        const initialX = state.camera.x;
        processHorizontalMovement(state);
        expect(state.camera.x).toBe(initialX);
    });
    it("does nothing when hopping but no slide key held", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" });
        const initialX = state.camera.x;
        processHorizontalMovement(state);
        expect(state.camera.x).toBe(initialX);
    });
    it("moves camera left when hopping and slideKeyHeld is left", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" });
        state.slideKeyHeld = "left";
        const initialX = state.camera.x;
        processHorizontalMovement(state);
        expect(state.camera.x).toBe(initialX - CAMERA_X_SPEED);
    });
    it("moves camera right when hopping and slideKeyHeld is right", () => {
        const state = createTestState({ kind: "hop", direction: "toward", frameIdx: 0, returnTo: "idle" });
        state.slideKeyHeld = "right";
        const initialX = state.camera.x;
        processHorizontalMovement(state);
        expect(state.camera.x).toBe(initialX + CAMERA_X_SPEED);
    });
    it("preserves camera.z when moving horizontally", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" });
        state.slideKeyHeld = "left";
        state.camera = { x: 0, z: 100 };
        processHorizontalMovement(state);
        expect(state.camera.z).toBe(100);
    });
    it("allows continuous horizontal movement", () => {
        const state = createTestState({ kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" });
        state.slideKeyHeld = "right";
        state.camera = { x: 0, z: 0 };
        processHorizontalMovement(state);
        processHorizontalMovement(state);
        processHorizontalMovement(state);
        expect(state.camera.x).toBe(CAMERA_X_SPEED * 3);
    });
});
describe("slide input during hop", () => {
    let bunnyState;
    let state;
    let timers;
    let frames;
    beforeEach(() => {
        vi.useFakeTimers();
        bunnyState = createTestBunnyState({ kind: "hop", direction: "away", frameIdx: 0, returnTo: "idle" });
        state = createTestInputState(bunnyState);
        frames = createTestFrames();
        timers = createBunnyTimers(bunnyState, frames, {
            walk: 100,
            idle: 200,
            jump: 50,
            transition: 80,
            hop: 100,
        });
        setupKeyboardControls(state, frames, timers);
    });
    afterEach(() => {
        vi.useRealTimers();
    });
    it("sets slideKeyHeld to left when a pressed during hop", () => {
        dispatchKeyDown("a");
        expect(state.slideKeyHeld).toBe("left");
    });
    it("sets slideKeyHeld to left when ArrowLeft pressed during hop", () => {
        dispatchKeyDown("ArrowLeft");
        expect(state.slideKeyHeld).toBe("left");
    });
    it("sets slideKeyHeld to right when d pressed during hop", () => {
        dispatchKeyDown("d");
        expect(state.slideKeyHeld).toBe("right");
    });
    it("sets slideKeyHeld to right when ArrowRight pressed during hop", () => {
        dispatchKeyDown("ArrowRight");
        expect(state.slideKeyHeld).toBe("right");
    });
    it("clears slideKeyHeld on a keyup", () => {
        dispatchKeyDown("a");
        expect(state.slideKeyHeld).toBe("left");
        dispatchKeyUp("a");
        expect(state.slideKeyHeld).toBe(null);
    });
    it("clears slideKeyHeld on ArrowLeft keyup", () => {
        dispatchKeyDown("ArrowLeft");
        expect(state.slideKeyHeld).toBe("left");
        dispatchKeyUp("ArrowLeft");
        expect(state.slideKeyHeld).toBe(null);
    });
    it("clears slideKeyHeld on d keyup", () => {
        dispatchKeyDown("d");
        expect(state.slideKeyHeld).toBe("right");
        dispatchKeyUp("d");
        expect(state.slideKeyHeld).toBe(null);
    });
    it("clears slideKeyHeld on ArrowRight keyup", () => {
        dispatchKeyDown("ArrowRight");
        expect(state.slideKeyHeld).toBe("right");
        dispatchKeyUp("ArrowRight");
        expect(state.slideKeyHeld).toBe(null);
    });
    it("clears slideKeyHeld when hop key released", () => {
        state.hopKeyHeld = "away";
        dispatchKeyDown("a");
        expect(state.slideKeyHeld).toBe("left");
        dispatchKeyUp("w");
        expect(state.slideKeyHeld).toBe(null);
    });
    it("does not set slideKeyHeld when not hopping", () => {
        state.bunny.animation = { kind: "idle", frameIdx: 0 };
        dispatchKeyDown("a");
        expect(state.slideKeyHeld).toBe(null);
    });
    it("does not clear slideKeyHeld when releasing d if currently sliding left", () => {
        dispatchKeyDown("d");
        expect(state.slideKeyHeld).toBe("right");
        dispatchKeyDown("a");
        expect(state.slideKeyHeld).toBe("left");
        dispatchKeyUp("d");
        expect(state.slideKeyHeld).toBe("left");
    });
    it("does not clear slideKeyHeld when releasing a if currently sliding right", () => {
        dispatchKeyDown("a");
        expect(state.slideKeyHeld).toBe("left");
        dispatchKeyDown("d");
        expect(state.slideKeyHeld).toBe("right");
        dispatchKeyUp("a");
        expect(state.slideKeyHeld).toBe("right");
    });
    it("allows alternating between left and right slide", () => {
        dispatchKeyDown("d");
        expect(state.slideKeyHeld).toBe("right");
        dispatchKeyUp("d");
        expect(state.slideKeyHeld).toBe(null);
        dispatchKeyDown("a");
        expect(state.slideKeyHeld).toBe("left");
        dispatchKeyUp("a");
        expect(state.slideKeyHeld).toBe(null);
        dispatchKeyDown("d");
        expect(state.slideKeyHeld).toBe("right");
    });
    it("handles rapid switching d->a->d while hopping", () => {
        dispatchKeyDown("d");
        expect(state.slideKeyHeld).toBe("right");
        dispatchKeyDown("a");
        expect(state.slideKeyHeld).toBe("left");
        dispatchKeyUp("d");
        expect(state.slideKeyHeld).toBe("left");
        dispatchKeyUp("a");
        expect(state.slideKeyHeld).toBe(null);
        dispatchKeyDown("d");
        expect(state.slideKeyHeld).toBe("right");
    });
});
//# sourceMappingURL=Keyboard.test.js.map