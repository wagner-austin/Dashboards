/**
 * Core type definitions for the ASCII animation engine.
 */

/** A set of frames at a specific width */
export interface FrameSet {
  readonly width: number;
  readonly frames: readonly string[];
}

/** Direction the sprite can face */
export type Direction = "left" | "right";

/** Animation state for the bunny */
export type BunnyState = "walk" | "jump" | "idle" | "alert";

/** A single animation with multiple size variants
 * The sizes Map uses string keys in format:
 * - "50" for single-direction sprites
 * - "50_left", "50_right" for multi-direction sprites
 */
export interface Animation {
  readonly name: string;
  readonly sizes: ReadonlyMap<string, FrameSet>;
  readonly directions: readonly Direction[];
}

/** A sprite with multiple animations */
export interface Sprite {
  readonly name: string;
  readonly animations: ReadonlyMap<string, Animation>;
  currentAnimation: string;
  currentFrame: number;
  currentSize: number;
  x: number;
  y: number;
  direction: Direction;
}

/** Layer type */
export type LayerType = "static" | "tile" | "sprites";

/** Configuration for a layer */
export interface LayerConfig {
  readonly name: string;
  readonly type: LayerType;
  readonly parallax: number;
  readonly sprites: readonly string[];
}

/** A layer containing sprites at the same depth */
export interface Layer {
  readonly name: string;
  readonly parallax: number;
  readonly sprites: Sprite[];
}

/** Sprite configuration from config.json */
export interface SpriteAnimationConfig {
  readonly source: string;
  readonly widths: readonly number[];
  readonly contrast: number;
  readonly invert: boolean;
  readonly crop?: string;
  readonly directions?: readonly Direction[];
}

/** Sprite definition with animations */
export interface SpriteConfig {
  readonly animations?: Record<string, SpriteAnimationConfig>;
  readonly source?: string;
  readonly widths?: readonly number[];
  readonly contrast?: number;
  readonly invert?: boolean;
}

/** Layer definition from config */
export interface LayerDefinition {
  readonly name: string;
  readonly type?: LayerType;
  readonly sprites?: readonly string[];
  readonly parallax?: number;
}

/** Global settings */
export interface Settings {
  readonly fps: number;
  readonly jumpSpeed: number;
  readonly scrollSpeed: number; // characters per second
}

/** Root config structure */
export interface Config {
  readonly sprites: Record<string, SpriteConfig>;
  readonly layers: readonly LayerDefinition[];
  readonly settings: Settings;
}
