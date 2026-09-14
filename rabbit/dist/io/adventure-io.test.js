/** @vitest-environment jsdom */
import { afterEach, describe, expect, it } from "vitest";
import { loadAdventureAssets } from "./adventure-io.js";
import { _test_hooks as transport } from "./transport.js";
import { createTestConfig, createTestAnimations, createTestAnimation } from "../testing/io-fixtures.js";
const originalImport = transport.importModule;
afterEach(() => { transport.importModule = originalImport; transport.clearSpriteModuleCache(); });
function config() {
    return { ...createTestConfig(), sprites: {
            bunny: { animations: { ...createTestAnimations(), alert: createTestAnimation(true, 40) } },
            lion: { animations: { ...createTestAnimations(), run: createTestAnimation(true, 64) } },
        } };
}
describe("adventure asset loading", () => {
    it("loads both characters through the real shared transport and keeps run separate", async () => {
        transport.importModule = (url) => Promise.resolve({ frames: [new URL(url).pathname] });
        const assets = await loadAdventureAssets(config(), "bunny");
        expect(assets.companion.walkLeft).toStrictEqual(["/dist/sprites/lion/walk/w50_left.js"]);
        expect(assets.lionSprint.left).toStrictEqual(["/dist/sprites/lion/run/w64_left.js"]);
        expect(assets.lionSprint.right).toStrictEqual(["/dist/sprites/lion/run/w64_right.js"]);
        expect(assets.alertLeft).toStrictEqual(["/dist/sprites/bunny/alert/w40_left.js"]);
        expect(assets.alertRight).toStrictEqual(["/dist/sprites/bunny/alert/w40_right.js"]);
        const lion = await loadAdventureAssets(config(), "lion");
        expect(lion.companion.walkLeft).toStrictEqual(["/dist/sprites/bunny/walk/w50_left.js"]);
    });
    it("rejects unsupported leaders before loading", async () => {
        await expect(loadAdventureAssets(config(), "bear")).rejects.toThrow("RABBIT_CHARACTER");
    });
    it("requires every part of the upright animation configuration", async () => {
        const base = config();
        const documents = [
            { ...base, sprites: {} },
            { ...base, sprites: { bunny: {} } },
            { ...base, sprites: { bunny: { animations: {} } } },
            { ...base, sprites: { bunny: { animations: { alert: { ...createTestAnimation(true, 40), widths: [] } } } } },
        ];
        for (const document of documents)
            await expect(loadAdventureAssets(document, "bunny")).rejects.toThrow("RABBIT_ALERT_CONFIG");
    });
    it("requires every part of the sprint animation configuration", async () => {
        const base = config();
        const documents = [
            { ...base, sprites: { bunny: { animations: { alert: createTestAnimation(true, 40) } } } },
            { ...base, sprites: { ...base.sprites, lion: {} } },
            { ...base, sprites: { ...base.sprites, lion: { animations: {} } } },
            { ...base, sprites: { ...base.sprites, lion: { animations: { run: { ...createTestAnimation(true, 64), widths: [] } } } } },
        ];
        for (const document of documents)
            await expect(loadAdventureAssets(document, "lion")).rejects.toThrow("RABBIT_RUN_CONFIG");
    });
});
//# sourceMappingURL=adventure-io.test.js.map