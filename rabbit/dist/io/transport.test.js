/**
 * @vitest-environment jsdom
 * Tests for the sprite transport: URL resolution, import caching, validation.
 *
 * This suite exists because `src/io/**` used to sit outside the coverage
 * denominator on the grounds that it was "tested through dependency
 * injection". It was not: DI meant main.ts's tests substituted fakes, so these
 * implementations never ran, and the 100% report was measuring a codebase with
 * 340 lines removed from it.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { assetUrl, loadSpriteFrames, loadStaticSpriteFrames, _test_hooks, } from "./transport.js";
const realImport = _test_hooks.importModule;
/** Every module URL the code under test asked for. */
let requested;
beforeEach(() => {
    requested = [];
    _test_hooks.clearSpriteModuleCache();
    _test_hooks.importModule = (url) => {
        requested.push(url);
        return Promise.resolve({ frames: [`frames:${new URL(url).pathname}`] });
    };
});
afterEach(() => {
    _test_hooks.importModule = realImport;
    _test_hooks.clearSpriteModuleCache();
});
describe("assetUrl", () => {
    it("resolves against the page, not the module", () => {
        // Bundling once moved the importing module and every sprite 404'd,
        // because a relative specifier resolves against the importer's URL.
        const url = new URL(assetUrl("dist/sprites/tree1/w40.js"));
        expect(url.origin).toBe(new URL(document.baseURI).origin);
        expect(url.pathname).toBe("/dist/sprites/tree1/w40.js");
    });
    it("carries a cache-busting query", () => {
        expect(new URL(assetUrl("config.json")).searchParams.get("v")).not.toBeNull();
    });
});
describe("loadSpriteFrames", () => {
    it("builds an undirected path when no direction is given", async () => {
        const result = await loadSpriteFrames("bunny", "hop_away", 40);
        expect(result.width).toBe(40);
        expect(requested[0]).toContain("dist/sprites/bunny/hop_away/w40.js");
    });
    it("suffixes the path with the direction when one is given", async () => {
        await loadSpriteFrames("bunny", "walk", 50, "left");
        expect(requested[0]).toContain("dist/sprites/bunny/walk/w50_left.js");
    });
    it("returns the module's frames", async () => {
        const result = await loadSpriteFrames("bunny", "idle", 40, "right");
        expect(result.frames).toEqual(["frames:/dist/sprites/bunny/idle/w40_right.js"]);
    });
    it("rejects a module with no frames array", async () => {
        _test_hooks.importModule = () => Promise.resolve({ frames: "not an array" });
        await expect(loadSpriteFrames("bunny", "walk", 50, "left")).rejects.toThrow("frames must be string array");
    });
});
describe("loadStaticSpriteFrames", () => {
    it("builds a path with no animation segment", async () => {
        const result = await loadStaticSpriteFrames("tree1", 40);
        expect(result.width).toBe(40);
        expect(requested[0]).toContain("dist/sprites/tree1/w40.js");
    });
});
describe("importSpriteModule caching", () => {
    it("imports a given path only once", async () => {
        await loadSpriteFrames("bunny", "walk", 50, "left");
        await loadSpriteFrames("bunny", "walk", 50, "left");
        expect(requested).toHaveLength(1);
    });
    it("serves concurrent requests for one path from a single import", async () => {
        // The promise is cached before it resolves, so a second caller arriving
        // mid-flight joins the first rather than starting another download.
        await Promise.all([
            loadSpriteFrames("bunny", "walk", 50, "left"),
            loadSpriteFrames("bunny", "walk", 50, "left"),
            loadSpriteFrames("bunny", "walk", 50, "left"),
        ]);
        expect(requested).toHaveLength(1);
    });
    it("keeps different paths apart", async () => {
        await loadSpriteFrames("bunny", "walk", 50, "left");
        await loadSpriteFrames("bunny", "walk", 50, "right");
        expect(requested).toHaveLength(2);
    });
});
describe("the real seams", () => {
    it("imports a module for real through the default importModule", async () => {
        // Exercises the seam itself rather than its substitute: a data: URL is a
        // real ES module the platform loader resolves without a network or a file.
        _test_hooks.importModule = realImport;
        const module = (await realImport("data:text/javascript,export const frames = ['x'];"));
        expect(module.frames).toEqual(["x"]);
    });
    it("delegates fetchFn to the platform fetch", async () => {
        const original = globalThis.fetch;
        let requestedUrl = "";
        globalThis.fetch = ((url) => {
            requestedUrl = url;
            return Promise.resolve({ ok: true });
        });
        try {
            const response = await _test_hooks.fetchFn("config.json");
            expect(requestedUrl).toBe("config.json");
            expect(response.ok).toBe(true);
        }
        finally {
            globalThis.fetch = original;
        }
    });
});
//# sourceMappingURL=transport.test.js.map