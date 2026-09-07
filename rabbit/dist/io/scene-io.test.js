/**
 * @vitest-environment jsdom
 * Tests for loading scenery: trees, grass, and layer-named sprites.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { loadTreeSizes, loadLayerSprites, loadGrassSprites, loadTreeSpritesProgressive, } from "./scene-io.js";
import { _test_hooks as transportHooks } from "./transport.js";
import { createMutableSpriteRegistry } from "../loaders/progressive.js";
import { createTestConfig, createTestValidatedLayer } from "../testing/io-fixtures.js";
const realImport = transportHooks.importModule;
/** Every module URL the loaders asked for. */
let requested;
beforeEach(() => {
    requested = [];
    transportHooks.clearSpriteModuleCache();
    transportHooks.importModule = (url) => {
        requested.push(url);
        return Promise.resolve({ frames: [`frames:${new URL(url).pathname}`] });
    };
});
afterEach(() => {
    transportHooks.importModule = realImport;
    transportHooks.clearSpriteModuleCache();
});
describe("loadTreeSizes", () => {
    it("returns one size per declared width, ascending", async () => {
        const sizes = await loadTreeSizes(createTestConfig());
        expect(sizes.map((s) => s.width)).toEqual([15, 40]);
    });
});
describe("loadLayerSprites", () => {
    it("loads each sprite a layer names, at every width", async () => {
        const registry = await loadLayerSprites(createTestConfig(), [
            createTestValidatedLayer("grass-front", ["grass"]),
        ]);
        expect(registry.sprites.get("grass")?.map((s) => s.width)).toEqual([160]);
    });
    it("loads a sprite named by two layers only once", async () => {
        await loadLayerSprites(createTestConfig(), [
            createTestValidatedLayer("a", ["grass"]),
            createTestValidatedLayer("b", ["grass"]),
        ]);
        expect(requested).toHaveLength(1);
    });
});
describe("loadGrassSprites", () => {
    it("reports progress for each width and populates the registry", async () => {
        const registry = createMutableSpriteRegistry(["grass"]);
        const progress = [];
        await loadGrassSprites(createTestConfig(), registry, (p) => progress.push(p));
        expect(progress.map((p) => p.phase)).toEqual(["grass"]);
        expect(registry.sprites.get("grass")).toHaveLength(1);
    });
});
describe("loadTreeSpritesProgressive", () => {
    it("loads smallest widths first, interleaved across tree types", async () => {
        const registry = createMutableSpriteRegistry(["tree1", "tree2"]);
        const progress = [];
        await loadTreeSpritesProgressive(createTestConfig(), registry, (p) => progress.push(p));
        // Smallest-first is what puts the far trees on screen before the near
        // ones, so the forest fills in from the horizon rather than popping.
        expect(progress.map((p) => p.width)).toEqual([15, 15, 40, 40]);
        expect(progress.every((p) => p.phase === "trees")).toBe(true);
    });
});
//# sourceMappingURL=scene-io.test.js.map