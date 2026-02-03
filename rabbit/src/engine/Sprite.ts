/**
 * Sprite management - loading frames and tracking state.
 */

import type { Sprite, Animation, FrameSet, Direction } from "../types.js";

/** Build the size key for looking up frame sets
 * For single-direction sprites: "50"
 * For multi-direction sprites: "50_left", "50_right"
 */
export function getSizeKey(
  size: number,
  direction: Direction,
  hasMultipleDirections: boolean
): string {
  if (hasMultipleDirections) {
    return `${String(size)}_${direction}`;
  }
  return String(size);
}

/** Create a new sprite instance */
export function createSprite(
  name: string,
  animations: ReadonlyMap<string, Animation>,
  initialAnimation: string,
  initialSize: number,
  x: number,
  y: number
): Sprite {
  return {
    name,
    animations,
    currentAnimation: initialAnimation,
    currentFrame: 0,
    currentSize: initialSize,
    x,
    y,
    direction: "right",
  };
}

/** Advance to the next frame in the current animation */
export function advanceFrame(sprite: Sprite): void {
  const animation = sprite.animations.get(sprite.currentAnimation);
  if (animation === undefined) return;

  const hasMultipleDirections = animation.directions.length > 1;
  const key = getSizeKey(sprite.currentSize, sprite.direction, hasMultipleDirections);
  const frameSet = animation.sizes.get(key);
  if (frameSet === undefined) return;

  sprite.currentFrame = (sprite.currentFrame + 1) % frameSet.frames.length;
}

/** Switch to a different animation */
export function setAnimation(sprite: Sprite, animationName: string): void {
  if (sprite.currentAnimation === animationName) return;

  const animation = sprite.animations.get(animationName);
  if (animation === undefined) return;

  sprite.currentAnimation = animationName;
  sprite.currentFrame = 0;
}

/** Extract the width number from a size key (e.g., "50" or "50_left" -> 50) */
function extractWidth(key: string): number {
  // Extract width from start of key before any underscore
  const underscoreIndex = key.indexOf("_");
  const widthStr = underscoreIndex === -1 ? key : key.slice(0, underscoreIndex);
  return parseInt(widthStr, 10);
}

/** Switch to a different size (for depth effect) */
export function setSize(sprite: Sprite, size: number): void {
  const animation = sprite.animations.get(sprite.currentAnimation);
  if (animation === undefined) return;

  // Extract unique widths from the keys
  const widths = new Set<number>();
  for (const key of animation.sizes.keys()) {
    widths.add(extractWidth(key));
  }

  const availableWidths = Array.from(widths);
  let closestWidth = availableWidths[0];
  if (closestWidth === undefined) return;

  let closestDiff = Math.abs(size - closestWidth);

  for (const width of availableWidths) {
    const diff = Math.abs(size - width);
    if (diff < closestDiff) {
      closestDiff = diff;
      closestWidth = width;
    }
  }

  sprite.currentSize = closestWidth;
}

/** Set sprite direction */
export function setDirection(sprite: Sprite, direction: Direction): void {
  sprite.direction = direction;
}

/** Build an Animation from frame sets */
export function buildAnimation(
  name: string,
  sizes: Map<string, FrameSet>,
  directions: readonly Direction[]
): Animation {
  return {
    name,
    sizes,
    directions,
  };
}
