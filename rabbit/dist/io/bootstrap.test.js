/**
 * Tests for the start-now-or-wait decision.
 */
import { describe, it, expect } from "vitest";
import { bootstrap } from "./bootstrap.js";
/** Build deps recording what bootstrap did, with a settable ready state. */
function createDeps(readyState, start = () => Promise.resolve()) {
    const deferred = [];
    const errors = [];
    let starts = 0;
    return {
        readyState: () => readyState,
        onDomReady: (handler) => {
            deferred.push(handler);
        },
        start: () => {
            starts++;
            return start();
        },
        onError: (error) => {
            errors.push(error);
        },
        deferred,
        errors,
        started: () => starts,
    };
}
describe("bootstrap", () => {
    it("starts immediately when the document is already complete", () => {
        const deps = createDeps("complete");
        bootstrap(deps);
        expect(deps.started()).toBe(1);
        expect(deps.deferred).toHaveLength(0);
    });
    it("starts immediately when the document is interactive", () => {
        const deps = createDeps("interactive");
        bootstrap(deps);
        expect(deps.started()).toBe(1);
    });
    it("waits for DOMContentLoaded while the document is still loading", () => {
        // Starting mid-parse would find no screen element.
        const deps = createDeps("loading");
        bootstrap(deps);
        expect(deps.started()).toBe(0);
        expect(deps.deferred).toHaveLength(1);
    });
    it("starts once the deferred callback fires", () => {
        const deps = createDeps("loading");
        bootstrap(deps);
        deps.deferred[0]?.();
        expect(deps.started()).toBe(1);
    });
    it("reports a rejected start rather than swallowing it", async () => {
        const failure = new Error("no screen");
        const deps = createDeps("complete", () => Promise.reject(failure));
        bootstrap(deps);
        await Promise.resolve();
        expect(deps.errors).toEqual([failure]);
    });
    it("reports a rejected deferred start too", async () => {
        const failure = new Error("no screen");
        const deps = createDeps("loading", () => Promise.reject(failure));
        bootstrap(deps);
        deps.deferred[0]?.();
        await Promise.resolve();
        expect(deps.errors).toEqual([failure]);
    });
});
//# sourceMappingURL=bootstrap.test.js.map