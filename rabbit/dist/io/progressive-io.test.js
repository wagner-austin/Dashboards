/**
 * @vitest-environment jsdom
 * Tests for the order sprites load in.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { runProgressiveLoad } from "./progressive-io.js";
import { _test_hooks as transportHooks } from "./transport.js";
import { createMutableSpriteRegistry } from "../loaders/progressive.js";
import { createTestConfig } from "../testing/io-fixtures.js";
const realImport = transportHooks.importModule;
beforeEach(() => {
    transportHooks.clearSpriteModuleCache();
    transportHooks.importModule = (url) => Promise.resolve({ frames: [`frames:${new URL(url).pathname}`] });
});
afterEach(() => {
    transportHooks.importModule = realImport;
    transportHooks.clearSpriteModuleCache();
});
describe("runProgressiveLoad", () => {
    it("runs the phases in order and hands over the character frames", async () => {
        const registry = createMutableSpriteRegistry(["grass", "tree1", "tree2"]);
        const phases = [];
        let handedOver = false;
        await runProgressiveLoad(createTestConfig(), "bunny", registry, (p) => {
            if (phases[phases.length - 1] !== p.phase)
                phases.push(p.phase);
        }, (frames) => {
            // Movement unlocks here, so this must fire before the trees load.
            handedOver = frames.walkLeft.length > 0;
            expect(phases[phases.length - 1]).toBe("bunny");
        });
        expect(phases).toEqual(["ground", "grass", "bunny", "trees"]);
        expect(handedOver).toBe(true);
    });
    it("reports the character it was asked for, not a hardcoded name", async () => {
        const registry = createMutableSpriteRegistry(["grass", "tree1", "tree2"]);
        const names = [];
        await runProgressiveLoad(createTestConfig(["lion"]), "lion", registry, (p) => {
            if (p.phase === "bunny")
                names.push(p.spriteName);
        }, () => {
            /* frames not needed here */
        });
        expect(names).toEqual(["lion"]);
    });
    it("populates the registry with the scenery it loaded", async () => {
        const registry = createMutableSpriteRegistry(["grass", "tree1", "tree2"]);
        await runProgressiveLoad(createTestConfig(), "bunny", registry, () => {
            /* progress not asserted here */
        }, () => {
            /* frames not asserted here */
        });
        expect(registry.sprites.get("grass")).toHaveLength(1);
        expect(registry.sprites.get("tree1")).toHaveLength(2);
    });
});
//# sourceMappingURL=progressive-io.test.js.map