/**
 * @vitest-environment jsdom
 * Tests for assembling a character's frames from config.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { loadCharacterFrames } from "./character-io.js";
import { _test_hooks as transportHooks } from "./transport.js";
import { createTestConfig } from "../testing/io-fixtures.js";
const realImport = transportHooks.importModule;
/** Every module URL the loader asked for. */
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
describe("loadCharacterFrames", () => {
    it("loads every animation at the width config declares", async () => {
        await loadCharacterFrames(createTestConfig(), "bunny");
        expect(requested.some((u) => u.includes("/walk/w50_left.js"))).toBe(true);
        expect(requested.some((u) => u.includes("/idle/w40_right.js"))).toBe(true);
        expect(requested.some((u) => u.includes("/hop_away/w40.js"))).toBe(true);
    });
    it("names the character in the path rather than hardcoding one", async () => {
        // The whole point of the refactor: a second character needs config and
        // art, not a code change.
        await loadCharacterFrames(createTestConfig(["lion"]), "lion");
        expect(requested).not.toHaveLength(0);
        expect(requested.every((u) => u.includes("/sprites/lion/"))).toBe(true);
    });
    it("gives the depth hops one frame set, not a left and a right", async () => {
        const frames = await loadCharacterFrames(createTestConfig(), "bunny");
        expect(frames.hopAway).toEqual(["frames:/dist/sprites/bunny/hop_away/w40.js"]);
        expect(frames.hopToward).toEqual(["frames:/dist/sprites/bunny/hop_toward/w40.js"]);
    });
    it("keeps left and right apart for directional animations", async () => {
        const frames = await loadCharacterFrames(createTestConfig(), "bunny");
        expect(frames.walkLeft).not.toEqual(frames.walkRight);
        expect(frames.walkLeft).toEqual(["frames:/dist/sprites/bunny/walk/w50_left.js"]);
        expect(frames.walkRight).toEqual(["frames:/dist/sprites/bunny/walk/w50_right.js"]);
    });
    it("fills every field the state machine reads", async () => {
        const frames = await loadCharacterFrames(createTestConfig(), "bunny");
        for (const [key, value] of Object.entries(frames)) {
            expect(value, key).toHaveLength(1);
        }
    });
    it("refuses a character config cannot satisfy", async () => {
        await expect(loadCharacterFrames(createTestConfig(), "lion")).rejects.toThrow('config.sprites has no character "lion"');
    });
    it("loads two characters from one config independently", async () => {
        const config = createTestConfig(["bunny", "lion"]);
        const bunny = await loadCharacterFrames(config, "bunny");
        const lion = await loadCharacterFrames(config, "lion");
        expect(bunny.walkLeft).not.toEqual(lion.walkLeft);
    });
});
//# sourceMappingURL=character-io.test.js.map