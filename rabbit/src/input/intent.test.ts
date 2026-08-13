/**
 * Tests for the movement intent value type.
 */

import { describe, it, expect } from "vitest";
import { _test_hooks } from "./intent.js";

const { createIntent, intentsEqual, isNeutralIntent, reverseHorizontal, facingToDirection, NEUTRAL_INTENT } =
  _test_hooks;

describe("NEUTRAL_INTENT", () => {
  it("requests no movement on either axis", () => {
    expect(NEUTRAL_INTENT.horizontal).toBeNull();
    expect(NEUTRAL_INTENT.vertical).toBeNull();
  });
});

describe("createIntent", () => {
  it("carries both axes through", () => {
    expect(createIntent("left", "up")).toStrictEqual({ horizontal: "left", vertical: "up" });
  });

  it("carries nulls through", () => {
    expect(createIntent(null, null)).toStrictEqual({ horizontal: null, vertical: null });
  });
});

describe("intentsEqual", () => {
  it("is true for matching axes", () => {
    expect(intentsEqual(createIntent("right", "down"), createIntent("right", "down"))).toBe(true);
  });

  it("is false when the horizontal axis differs", () => {
    expect(intentsEqual(createIntent("right", "down"), createIntent("left", "down"))).toBe(false);
  });

  it("is false when the vertical axis differs", () => {
    expect(intentsEqual(createIntent("right", "down"), createIntent("right", "up"))).toBe(false);
  });

  it("is true for two neutral intents", () => {
    expect(intentsEqual(NEUTRAL_INTENT, createIntent(null, null))).toBe(true);
  });
});

describe("isNeutralIntent", () => {
  it("is true when both axes are null", () => {
    expect(isNeutralIntent(createIntent(null, null))).toBe(true);
  });

  it("is false when only horizontal is set", () => {
    expect(isNeutralIntent(createIntent("left", null))).toBe(false);
  });

  it("is false when only vertical is set", () => {
    expect(isNeutralIntent(createIntent(null, "up"))).toBe(false);
  });
});

describe("reverseHorizontal", () => {
  it("turns left into right", () => {
    expect(reverseHorizontal("left")).toBe("right");
  });

  it("turns right into left", () => {
    expect(reverseHorizontal("right")).toBe("left");
  });
});

describe("facingToDirection", () => {
  it("maps facing right to right", () => {
    expect(facingToDirection(true)).toBe("right");
  });

  it("maps facing left to left", () => {
    expect(facingToDirection(false)).toBe("left");
  });
});
