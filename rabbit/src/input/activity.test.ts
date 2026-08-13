/**
 * Tests for the user activity tracker.
 */

import { describe, it, expect } from "vitest";
import { _test_hooks } from "./activity.js";

const { createActivityTracker } = _test_hooks;

describe("createActivityTracker", () => {
  it("starts with no idle time", () => {
    expect(createActivityTracker().idleSeconds()).toBe(0);
  });

  it("accumulates advanced time", () => {
    const activity = createActivityTracker();
    activity.advance(0.5);
    activity.advance(0.25);
    expect(activity.idleSeconds()).toBe(0.75);
  });

  it("resets to zero when activity is recorded", () => {
    const activity = createActivityTracker();
    activity.advance(4);
    activity.record();
    expect(activity.idleSeconds()).toBe(0);
  });

  it("resumes accumulating after a reset", () => {
    const activity = createActivityTracker();
    activity.advance(4);
    activity.record();
    activity.advance(1.5);
    expect(activity.idleSeconds()).toBe(1.5);
  });

  it("keeps trackers independent", () => {
    const first = createActivityTracker();
    const second = createActivityTracker();
    first.advance(3);
    expect(second.idleSeconds()).toBe(0);
    expect(first.idleSeconds()).toBe(3);
  });
});
