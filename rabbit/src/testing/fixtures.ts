/**
 * Shared test fixtures for the input layer.
 *
 * These are real implementations, not stand-ins: the frame data is real frame
 * data, the event sources really store and replay handlers, and the draw
 * source really returns the sequence it was given. Nothing here fakes the
 * behaviour under test - it only supplies inputs that would otherwise be
 * duplicated across every suite.
 */

import {
  createBunnyTimers,
  type AnimationState,
  type BunnyFrames,
  type BunnyState,
  type BunnyTimers,
} from "../entities/Bunny.js";
import type { RandomSource } from "../input/Autopilot.js";
import type { KeyEventType, KeyboardEventSource } from "../input/Keyboard.js";
import { createInputState, type InputState } from "../input/state.js";
import type { TouchEventSource, TouchEventType, TouchPoint } from "../input/Touch.js";
import type { LayerInstance, SceneSpriteState, ValidatedLayer } from "../layers/types.js";
import { layerToWorldZ } from "../layers/widths.js";
import { LAYER_BEHAVIORS, type FrameSet, type LayerBehavior } from "../types.js";
import { calculateDepthBounds, createProjectionConfig, type DepthBounds } from "../world/Projection.js";

/**
 * Build a single-size frame set from one frame of art.
 *
 * Args:
 *     frame: Newline-separated glyph rows for the sole frame.
 *     width: Character width of the frame.
 *
 * Returns:
 *     A one-entry FrameSet list, matching the shape sprites carry at runtime.
 */
export function createTestSizes(
  frame = "ABC\nDEF",
  width = 3
): FrameSet[] {
  return [{ width, frames: [frame] }];
}

/**
 * Build a scene sprite positioned in world space.
 *
 * Args:
 *     worldX: Horizontal world position.
 *     worldZ: Depth. Compare against layerToWorldZ to reason about occlusion.
 *     sizes: Frame sets the sprite draws from.
 *
 * Returns:
 *     A SceneSpriteState at the requested position.
 */
export function createTestEntity(
  worldX: number,
  worldZ: number,
  sizes: FrameSet[] = createTestSizes()
): SceneSpriteState {
  return {
    spriteName: "test",
    sizes,
    sizeIdx: 0,
    frameIdx: 0,
    worldX,
    worldZ,
  };
}

/**
 * Build a sprite layer holding the given entities.
 *
 * Args:
 *     name: Layer name. A name containing "front" routes it to the foreground pass.
 *     zIndex: Draw index within its pass.
 *     layer: Layer number, convertible to depth via layerToWorldZ.
 *     entities: Sprites the layer owns.
 *     positions: World X positions declared by config.
 *     behavior: Wrapping behavior for the layer.
 *
 * Returns:
 *     A LayerInstance ready to hand to the renderer.
 */
export function createTestLayer(
  name: string,
  zIndex: number,
  layer: number,
  entities: SceneSpriteState[],
  positions: readonly number[] = [],
  behavior: LayerBehavior = LAYER_BEHAVIORS.midground
): LayerInstance {
  const config: ValidatedLayer = {
    name,
    type: "sprites",
    layer,
    spriteNames: [],
    positions,
    zIndex,
    tile: false,
    behavior,
  };
  return { config, entities };
}

/**
 * Create bunny frames with distinguishable labels per animation.
 *
 * Returns:
 *     BunnyFrames whose entries identify the animation and index they came from.
 */
export function createTestFrames(): BunnyFrames {
  return {
    walkLeft: ["walkL0", "walkL1"],
    walkRight: ["walkR0", "walkR1"],
    jumpLeft: ["jumpL0"],
    jumpRight: ["jumpR0"],
    idleLeft: ["idleL0"],
    idleRight: ["idleR0"],
    walkToIdleLeft: ["transL0", "transL1", "transL2"],
    walkToIdleRight: ["transR0", "transR1", "transR2"],
    walkToTurnAwayLeft: ["turnAwayL0", "turnAwayL1"],
    walkToTurnAwayRight: ["turnAwayR0", "turnAwayR1"],
    walkToTurnTowardLeft: ["turnTowardL0", "turnTowardL1"],
    walkToTurnTowardRight: ["turnTowardR0", "turnTowardR1"],
    hopAway: ["hopAway0", "hopAway1"],
    hopToward: ["hopToward0", "hopToward1"],
  };
}

/**
 * Create bunny state in a chosen animation.
 *
 * Args:
 *     animation: Animation state to start in.
 *     facingRight: Direction the bunny faces.
 *
 * Returns:
 *     BunnyState in that animation.
 */
export function createTestBunnyState(
  animation: AnimationState,
  facingRight = false
): BunnyState {
  return { facingRight, animation };
}

/**
 * Create depth bounds matching the shipped layer range of 8 to 30.
 *
 * Returns:
 *     DepthBounds derived from the real projection maths.
 */
export function createTestDepthBounds(): DepthBounds {
  const projectionConfig = createProjectionConfig();
  return calculateDepthBounds(layerToWorldZ(8), layerToWorldZ(30), projectionConfig);
}

/**
 * Create input state around a bunny, with a neutral intent.
 *
 * Args:
 *     bunny: Bunny state to wrap.
 *
 * Returns:
 *     InputState positioned at the origin.
 */
export function createTestInputState(bunny: BunnyState): InputState {
  return createInputState(
    bunny,
    { width: 100, height: 50, charW: 10, charH: 20 },
    { x: 0, z: 0 },
    createTestDepthBounds()
  );
}

/**
 * Create real bunny animation timers with short intervals.
 *
 * Args:
 *     bunny: Bunny state the timers advance.
 *     frames: Animation frames the timers step through.
 *     isHorizontalHeld: Callback deciding what completion settles into.
 *
 * Returns:
 *     BunnyTimers wired to the given state.
 */
export function createTestTimers(
  bunny: BunnyState,
  frames: BunnyFrames,
  isHorizontalHeld: () => boolean
): BunnyTimers {
  return createBunnyTimers(
    bunny,
    frames,
    { walk: 100, idle: 200, jump: 50, transition: 80, hop: 100 },
    isHorizontalHeld
  );
}

/**
 * Create a draw source that replays a fixed sequence.
 *
 * Exhausting the sequence throws rather than wrapping or returning a default,
 * so a test that consumes more draws than it declared fails loudly instead of
 * silently exercising a different branch.
 *
 * Args:
 *     draws: Values to return in order.
 *
 * Returns:
 *     RandomSource over that sequence.
 *
 * Raises:
 *     Error: When called more times than there are draws.
 */
export function createSequenceRandom(draws: readonly number[]): RandomSource {
  let index = 0;
  return (): number => {
    const value = draws[index];
    if (value === undefined) {
      throw new Error(`sequence random exhausted after ${String(draws.length)} draws`);
    }
    index += 1;
    return value;
  };
}

/**
 * Create a draw source that always returns the same value.
 *
 * Args:
 *     value: Value to return for every draw.
 *
 * Returns:
 *     RandomSource returning that value.
 */
export function createConstantRandom(value: number): RandomSource {
  return (): number => value;
}

/** Keyboard event source that replays presses to the bound handlers. */
export interface TestKeyboardSource extends KeyboardEventSource {
  /** Dispatch a keydown and return the event, for asserting preventDefault. */
  readonly press: (key: string, repeat?: boolean) => KeyboardEvent;
  /** Dispatch a keyup and return the event. */
  readonly release: (key: string) => KeyboardEvent;
  /** Number of handlers bound per event type. */
  readonly boundCount: (type: KeyEventType) => number;
}

/**
 * Create a keyboard event source backed by real KeyboardEvent objects.
 *
 * Returns:
 *     TestKeyboardSource able to dispatch presses to bound handlers.
 */
export function createTestKeyboardSource(): TestKeyboardSource {
  const handlers = new Map<KeyEventType, ((event: KeyboardEvent) => void)[]>();

  const emit = (type: KeyEventType, event: KeyboardEvent): KeyboardEvent => {
    for (const handler of handlers.get(type) ?? []) {
      handler(event);
    }
    return event;
  };

  return {
    addKeyListener: (type: KeyEventType, handler: (event: KeyboardEvent) => void): void => {
      const existing = handlers.get(type) ?? [];
      existing.push(handler);
      handlers.set(type, existing);
    },
    press: (key: string, repeat = false): KeyboardEvent =>
      emit("keydown", new KeyboardEvent("keydown", { key, repeat, cancelable: true })),
    release: (key: string): KeyboardEvent =>
      emit("keyup", new KeyboardEvent("keyup", { key, cancelable: true })),
    boundCount: (type: KeyEventType): number => (handlers.get(type) ?? []).length,
  };
}

/** Touch event source that replays touch points to the bound handlers. */
export interface TestTouchSource extends TouchEventSource {
  /** Dispatch touch points and return whether a handler consumed them. */
  readonly emit: (type: TouchEventType, points: readonly TouchPoint[]) => boolean;
  /** Set the timestamp returned by `now`. */
  readonly setNow: (value: number) => void;
  /** Passive flag recorded for a bound event type. */
  readonly passiveFor: (type: TouchEventType) => boolean | undefined;
}

/**
 * Create a touch event source over plain touch points.
 *
 * Returns:
 *     TestTouchSource able to dispatch points to bound handlers.
 */
export function createTestTouchSource(): TestTouchSource {
  const handlers = new Map<TouchEventType, ((points: readonly TouchPoint[]) => boolean)[]>();
  const passive = new Map<TouchEventType, boolean>();
  let clock = 0;

  return {
    addTouchListener: (
      type: TouchEventType,
      handler: (points: readonly TouchPoint[]) => boolean,
      isPassive: boolean
    ): void => {
      const existing = handlers.get(type) ?? [];
      existing.push(handler);
      handlers.set(type, existing);
      passive.set(type, isPassive);
    },
    now: (): number => clock,
    emit: (type: TouchEventType, points: readonly TouchPoint[]): boolean => {
      let consumed = false;
      for (const handler of handlers.get(type) ?? []) {
        if (handler(points)) {
          consumed = true;
        }
      }
      return consumed;
    },
    setNow: (value: number): void => {
      clock = value;
    },
    passiveFor: (type: TouchEventType): boolean | undefined => passive.get(type),
  };
}
