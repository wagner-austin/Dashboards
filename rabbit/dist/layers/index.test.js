/**
 * Tests for layer system exports.
 * Verifies all public exports are accessible.
 */
import { describe, it, expect } from "vitest";
import { createSceneState, validateLayersConfig, renderLayer, renderAllLayers, renderForegroundLayers, } from "./index.js";
describe("layers/index exports", () => {
    it("exports createSceneState", () => {
        expect(typeof createSceneState).toBe("function");
    });
    it("exports validateLayersConfig", () => {
        expect(typeof validateLayersConfig).toBe("function");
    });
    it("exports renderLayer", () => {
        expect(typeof renderLayer).toBe("function");
    });
    it("exports renderAllLayers", () => {
        expect(typeof renderAllLayers).toBe("function");
    });
    it("exports renderForegroundLayers", () => {
        expect(typeof renderForegroundLayers).toBe("function");
    });
});
//# sourceMappingURL=index.test.js.map