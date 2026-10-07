import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createBunnyTimers, getJumpLift, type BunnyFrames } from "./Bunny.js";
import { handleJumpInput } from "../input/handlers.js";
import { createTestBunnyState, createTestFrames } from "../testing/fixtures.js";

const intervals = { walk: 120, idle: 500, jump: 58, transition: 85, hop: 150 };

function jumpFrames(): BunnyFrames {
  return {
    ...createTestFrames(),
    jumpLeft: ["stand", "crouch", "takeoff", "airborne", "landing", "stand"],
    jumpRight: ["stand", "crouch", "takeoff", "airborne", "landing", "stand"],
    jumpMotion: { durationMs: 720, heightRows: 8 },
  };
}

describe("character jump motion", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it.each([false, true])("jumps immediately and lands based on movement intent (%s)", (moving) => {
    const state = createTestBunnyState({ kind: moving ? "walk" : "idle", frameIdx: 0 });
    const frames = jumpFrames();
    const timers = createBunnyTimers(state, frames, intervals, () => moving);
    handleJumpInput(state, frames, timers);
    expect(state.animation.kind).toBe("jump");
    expect(timers.transition.isRunning()).toBe(false);
    const startedAt = performance.now();
    expect(getJumpLift(state, frames, startedAt)).toBe(0);
    expect(getJumpLift(state, frames, startedAt + 240)).toBe(0);
    expect(getJumpLift(state, frames, startedAt + 420)).toBeCloseTo(8);
    expect(getJumpLift(state, frames, startedAt + 600)).toBe(0);
    vi.advanceTimersByTime(360);
    expect(state.animation.frameIdx).toBe(3);
    vi.advanceTimersByTime(360);
    expect(state.animation).toEqual({ kind: moving ? "walk" : "idle", frameIdx: 0 });
    expect(timers.jump.isRunning()).toBe(false);
    expect(getJumpLift(state, frames, startedAt + 720)).toBe(0);
  });

  it("retains the original rabbit's baked-in jump and transition timing", () => {
    const state = createTestBunnyState({ kind: "idle", frameIdx: 0 });
    const frames = createTestFrames();
    const timers = createBunnyTimers(state, frames, intervals, () => false);
    handleJumpInput(state, frames, timers);
    expect(state.animation.kind).toBe("transition");
    expect(getJumpLift(state, frames, 400)).toBe(0);
  });

  it("interrupts a transition to jump straight away", () => {
    const state = createTestBunnyState({
      kind: "transition",
      type: "walk_to_idle",
      frameIdx: 1,
      pendingAction: null,
      returnTo: "idle",
    });
    const frames = jumpFrames();
    const timers = createBunnyTimers(state, frames, intervals, () => false);
    timers.transition.start();
    handleJumpInput(state, frames, timers);
    expect(state.animation).toMatchObject({ kind: "jump", frameIdx: 0 });
    expect(timers.transition.isRunning()).toBe(false);
    expect(timers.jump.isRunning()).toBe(true);
  });

  it("ignores jump input mid-hop even with a jump motion", () => {
    const state = createTestBunnyState({ kind: "hop", direction: "away", frameIdx: 2 });
    const frames = jumpFrames();
    const timers = createBunnyTimers(state, frames, intervals, () => false);
    handleJumpInput(state, frames, timers);
    expect(state.animation).toEqual({ kind: "hop", direction: "away", frameIdx: 2 });
    expect(timers.jump.isRunning()).toBe(false);
  });

  it("never displaces a jump with no start time or a grounded state", () => {
    const frames = jumpFrames();
    expect(getJumpLift(createTestBunnyState({ kind: "jump", frameIdx: 0 }), frames, 400)).toBe(0);
    expect(getJumpLift(createTestBunnyState({ kind: "idle", frameIdx: 0 }), frames, 400)).toBe(0);
  });
});
