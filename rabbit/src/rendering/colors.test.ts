/**
 * Tests for render layer colour validation.
 */

import { describe, it, expect } from "vitest";
import {
  validateColorsConfig,
  DEFAULT_LAYER_COLORS,
  _test_hooks,
  type LayerColors,
} from "./colors.js";

const { isRecord, requireColor } = _test_hooks;

describe("validateColorsConfig", () => {
  it("returns the defaults when the block is absent", () => {
    expect(validateColorsConfig(undefined)).toEqual(DEFAULT_LAYER_COLORS);
  });

  it("defaults every layer to the pre-split single colour", () => {
    // A config with no colours block must render identically to the engine
    // before the scene was split across three elements.
    expect(DEFAULT_LAYER_COLORS).toEqual({
      world: "#e0e0e0",
      actor: "#e0e0e0",
      foreground: "#e0e0e0",
    });
  });

  it("reads all three layers", () => {
    const result = validateColorsConfig({
      world: "#111111",
      actor: "#6db3ff",
      foreground: "#222222",
    });

    expect(result).toEqual({
      world: "#111111",
      actor: "#6db3ff",
      foreground: "#222222",
    });
  });

  it("fills absent fields from the defaults, keeping the rest", () => {
    const result: LayerColors = validateColorsConfig({ actor: "#6db3ff" });

    expect(result.actor).toBe("#6db3ff");
    expect(result.world).toBe(DEFAULT_LAYER_COLORS.world);
    expect(result.foreground).toBe(DEFAULT_LAYER_COLORS.foreground);
  });

  it("accepts non-hex CSS colour syntax", () => {
    // The browser is the authority on colour syntax, not this validator.
    const result = validateColorsConfig({
      world: "rgb(10, 10, 10)",
      actor: "hsl(210 100% 70%)",
      foreground: "rebeccapurple",
    });

    expect(result.actor).toBe("hsl(210 100% 70%)");
    expect(result.foreground).toBe("rebeccapurple");
  });

  it("rejects a non-object block", () => {
    expect(() => validateColorsConfig("#6db3ff")).toThrow("colors: must be an object");
  });

  it("rejects an array block", () => {
    expect(() => validateColorsConfig(["#6db3ff"])).toThrow("colors: must be an object");
  });

  it("rejects a null block", () => {
    expect(() => validateColorsConfig(null)).toThrow("colors: must be an object");
  });

  it("rejects a non-string colour", () => {
    expect(() => validateColorsConfig({ actor: 255 })).toThrow(
      'colors: "actor" must be a non-empty string'
    );
  });

  it("rejects an empty colour", () => {
    expect(() => validateColorsConfig({ world: "" })).toThrow(
      'colors: "world" must be a non-empty string'
    );
  });

  it("rejects a whitespace-only colour", () => {
    // "   " would silently produce an invalid CSS declaration the browser
    // drops, leaving the layer with an inherited colour and no error.
    expect(() => validateColorsConfig({ foreground: "   " })).toThrow(
      'colors: "foreground" must be a non-empty string'
    );
  });
});

describe("isRecord", () => {
  it("accepts a plain object", () => {
    expect(isRecord({ actor: "#fff" })).toBe(true);
  });

  it("rejects null", () => {
    expect(isRecord(null)).toBe(false);
  });

  it("rejects an array", () => {
    expect(isRecord([])).toBe(false);
  });

  it("rejects a primitive", () => {
    expect(isRecord("#fff")).toBe(false);
  });
});

describe("requireColor", () => {
  it("returns the fallback when absent", () => {
    expect(requireColor(undefined, "actor", "#e0e0e0")).toBe("#e0e0e0");
  });

  it("returns the value when present", () => {
    expect(requireColor("#6db3ff", "actor", "#e0e0e0")).toBe("#6db3ff");
  });

  it("names the field it rejected", () => {
    expect(() => requireColor(42, "world", "#e0e0e0")).toThrow(
      'colors: "world" must be a non-empty string'
    );
  });
});
