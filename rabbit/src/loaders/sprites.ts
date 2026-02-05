/**
 * Sprite loading and animation timer utilities.
 */

import type { Config, FrameSet } from "../types.js";

export async function loadSpriteFrames(
  spriteName: string,
  animationName: string,
  width: number,
  direction?: string
): Promise<FrameSet> {
  const suffix = direction !== undefined ? `_${direction}` : "";
  const module = (await import(
    `../sprites/${spriteName}/${animationName}/w${String(width)}${suffix}.js`
  )) as { frames: readonly string[] };
  return {
    width,
    frames: module.frames,
  };
}

export async function loadStaticSpriteFrames(
  spriteName: string,
  width: number
): Promise<FrameSet> {
  const module = (await import(
    `../sprites/${spriteName}/w${String(width)}.js`
  )) as { frames: readonly string[] };
  return {
    width,
    frames: module.frames,
  };
}

export async function loadConfig(): Promise<Config> {
  const response = await fetch("./config.json");
  return (await response.json()) as Config;
}

/** Animation timer interface */
export interface AnimationTimer {
  start: () => void;
  stop: () => void;
  isRunning: () => boolean;
}

export function createAnimationTimer(
  intervalMs: number,
  onTick: () => void
): AnimationTimer {
  let id: ReturnType<typeof setInterval> | null = null;

  return {
    start(): void {
      if (id !== null) return;
      id = setInterval(onTick, intervalMs);
    },
    stop(): void {
      if (id !== null) {
        clearInterval(id);
        id = null;
      }
    },
    isRunning(): boolean {
      return id !== null;
    },
  };
}
