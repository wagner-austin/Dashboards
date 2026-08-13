/**
 * @vitest-environment jsdom
 * Tests for the shared test fixtures.
 *
 * The fixtures are real implementations that the input suites depend on, so
 * their own contracts - especially the draw sequence running out - are
 * asserted here rather than assumed.
 */
import { describe, it, expect } from "vitest";
import { createConstantRandom, createSequenceRandom, createTestBunnyState, createTestDepthBounds, createTestFrames, createTestInputState, createTestKeyboardSource, createTestTimers, createTestTouchSource, } from "./fixtures.js";
describe("createSequenceRandom", () => {
    it("replays the sequence in order", () => {
        const random = createSequenceRandom([0.1, 0.2, 0.3]);
        expect(random()).toBe(0.1);
        expect(random()).toBe(0.2);
        expect(random()).toBe(0.3);
    });
    it("throws once the sequence is exhausted", () => {
        const random = createSequenceRandom([0.1]);
        random();
        expect(() => random()).toThrow("sequence random exhausted after 1 draws");
    });
    it("throws immediately when given no draws", () => {
        expect(() => createSequenceRandom([])()).toThrow("sequence random exhausted after 0 draws");
    });
});
describe("createConstantRandom", () => {
    it("returns the same value every time", () => {
        const random = createConstantRandom(0.25);
        expect(random()).toBe(0.25);
        expect(random()).toBe(0.25);
    });
});
describe("createTestFrames", () => {
    it("supplies a non-empty frame list for every animation", () => {
        const frames = createTestFrames();
        const named = [
            ["walkLeft", frames.walkLeft],
            ["walkRight", frames.walkRight],
            ["jumpLeft", frames.jumpLeft],
            ["jumpRight", frames.jumpRight],
            ["idleLeft", frames.idleLeft],
            ["idleRight", frames.idleRight],
            ["walkToIdleLeft", frames.walkToIdleLeft],
            ["walkToIdleRight", frames.walkToIdleRight],
            ["walkToTurnAwayLeft", frames.walkToTurnAwayLeft],
            ["walkToTurnAwayRight", frames.walkToTurnAwayRight],
            ["walkToTurnTowardLeft", frames.walkToTurnTowardLeft],
            ["walkToTurnTowardRight", frames.walkToTurnTowardRight],
            ["hopAway", frames.hopAway],
            ["hopToward", frames.hopToward],
        ];
        for (const [name, list] of named) {
            expect(list.length, `${name} should have frames`).toBeGreaterThan(0);
        }
    });
});
describe("createTestBunnyState", () => {
    it("defaults to facing left", () => {
        expect(createTestBunnyState({ kind: "idle", frameIdx: 0 }).facingRight).toBe(false);
    });
    it("honours an explicit facing", () => {
        expect(createTestBunnyState({ kind: "idle", frameIdx: 0 }, true).facingRight).toBe(true);
    });
});
describe("createTestDepthBounds", () => {
    it("spans a real range derived from the projection", () => {
        const bounds = createTestDepthBounds();
        expect(bounds.minZ).toBeLessThan(bounds.maxZ);
        expect(bounds.range).toBeGreaterThan(0);
    });
});
describe("createTestInputState", () => {
    it("wraps the supplied bunny with a neutral intent", () => {
        const bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        const state = createTestInputState(bunny);
        expect(state.bunny).toBe(bunny);
        expect(state.intent).toStrictEqual({ horizontal: null, vertical: null });
    });
});
describe("createTestTimers", () => {
    it("builds timers that are not yet running", () => {
        const bunny = createTestBunnyState({ kind: "idle", frameIdx: 0 });
        const timers = createTestTimers(bunny, createTestFrames(), () => false);
        expect(timers.walk.isRunning()).toBe(false);
        expect(timers.idle.isRunning()).toBe(false);
    });
});
describe("createTestKeyboardSource", () => {
    it("reports nothing bound before listeners are added", () => {
        const source = createTestKeyboardSource();
        expect(source.boundCount("keydown")).toBe(0);
        expect(source.boundCount("keyup")).toBe(0);
    });
    it("dispatches to bound listeners only", () => {
        const source = createTestKeyboardSource();
        const seen = [];
        source.addKeyListener("keydown", (event) => seen.push(event.key));
        source.press("a");
        source.release("a");
        expect(seen).toStrictEqual(["a"]);
        expect(source.boundCount("keydown")).toBe(1);
    });
    it("dispatches releases to keyup listeners", () => {
        const source = createTestKeyboardSource();
        const seen = [];
        source.addKeyListener("keyup", (event) => seen.push(event.key));
        source.release("d");
        expect(seen).toStrictEqual(["d"]);
    });
    it("marks auto-repeat when asked", () => {
        const source = createTestKeyboardSource();
        expect(source.press("a").repeat).toBe(false);
        expect(source.press("a", true).repeat).toBe(true);
    });
    it("emits cancellable events so preventDefault is observable", () => {
        const source = createTestKeyboardSource();
        source.addKeyListener("keydown", (event) => {
            event.preventDefault();
        });
        expect(source.press(" ").defaultPrevented).toBe(true);
    });
});
describe("createTestTouchSource", () => {
    it("reports no passive flag before listeners are added", () => {
        expect(createTestTouchSource().passiveFor("touchmove")).toBeUndefined();
    });
    it("reports no consumption when nothing is bound", () => {
        expect(createTestTouchSource().emit("touchmove", [])).toBe(false);
    });
    it("records the passive flag per event type", () => {
        const source = createTestTouchSource();
        source.addTouchListener("touchmove", () => true, false);
        source.addTouchListener("touchstart", () => false, true);
        expect(source.passiveFor("touchmove")).toBe(false);
        expect(source.passiveFor("touchstart")).toBe(true);
    });
    it("reports consumption when a listener claims the gesture", () => {
        const source = createTestTouchSource();
        source.addTouchListener("touchmove", () => false, false);
        source.addTouchListener("touchmove", () => true, false);
        expect(source.emit("touchmove", [{ identifier: 1, clientX: 0, clientY: 0 }])).toBe(true);
    });
    it("reports no consumption when every listener declines", () => {
        const source = createTestTouchSource();
        source.addTouchListener("touchmove", () => false, false);
        expect(source.emit("touchmove", [])).toBe(false);
    });
    it("starts its clock at zero and follows setNow", () => {
        const source = createTestTouchSource();
        expect(source.now()).toBe(0);
        source.setNow(750);
        expect(source.now()).toBe(750);
    });
    it("passes the emitted points through to listeners", () => {
        const source = createTestTouchSource();
        let received = 0;
        source.addTouchListener("touchstart", (points) => {
            received = points.length;
            return false;
        }, true);
        source.emit("touchstart", [
            { identifier: 1, clientX: 10, clientY: 20 },
            { identifier: 2, clientX: 30, clientY: 40 },
        ]);
        expect(received).toBe(2);
    });
});
//# sourceMappingURL=fixtures.test.js.map