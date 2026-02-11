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
/**
 * Layer behavior configuration.
 *
 * Controls how a layer responds to camera movement.
 *
 * parallax: Camera tracking multiplier (0 = fixed, 1 = full tracking).
 * wrapX: Whether entities wrap horizontally for infinite scroll.
 * wrapZ: Whether entities wrap in depth for infinite depth scroll.
 */
export interface LayerBehavior {
    readonly parallax: number;
    readonly wrapX: boolean;
    readonly wrapZ: boolean;
}
/**
 * Preset layer behaviors for common layer types.
 */
export declare const LAYER_BEHAVIORS: {
    /** Sky/background - fixed, no wrapping */
    readonly static: {
        readonly parallax: 0;
        readonly wrapX: false;
        readonly wrapZ: false;
    };
    /** Distant mountains - slow parallax, no wrapping */
    readonly background: {
        readonly parallax: 0.3;
        readonly wrapX: false;
        readonly wrapZ: false;
    };
    /** Trees/objects - full tracking, X wrap for infinite scroll */
    readonly midground: {
        readonly parallax: 1;
        readonly wrapX: true;
        readonly wrapZ: false;
    };
    /** Ground plane - full tracking, X wrap, tiles horizontally */
    readonly foreground: {
        readonly parallax: 1;
        readonly wrapX: true;
        readonly wrapZ: false;
    };
};
/** Configuration for a layer */
export interface LayerConfig {
    readonly name: string;
    readonly type: LayerType;
    readonly depth: number;
    readonly sprites: readonly string[];
}
/** A layer containing sprites at the same depth */
export interface Layer {
    readonly name: string;
    readonly depth: number;
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
/**
 * Layer-based sprite configuration.
 *
 * Defines how a sprite scales across layers with automatic width generation.
 * Widths are generated using a decreasing step formula (fine steps for small
 * sizes, coarse steps for large sizes).
 *
 * minWidth: Smallest character width (most distant layer).
 * maxWidth: Largest character width (closest layer).
 * defaultLayer: Layer where third largest size appears.
 * layerDepth: Number of layers/sizes the sprite spans.
 */
export interface LayerSpriteConfig {
    readonly minWidth: number;
    readonly maxWidth: number;
    readonly defaultLayer: number;
    readonly layerDepth: number;
}
/**
 * Zoom configuration for depth-based sprites like trees.
 *
 * Defines the visual range from horizon (far/small) to foreground (close/large).
 * Sprite widths are auto-calculated by lerping between minWidth and maxWidth.
 *
 * horizonY: Y position at horizon (0-1, from top).
 * foregroundY: Y position in foreground (0-1, from top).
 * minWidth: Sprite width at horizon (smallest).
 * maxWidth: Sprite width in foreground (largest).
 * steps: Number of zoom levels (0 = horizon, steps = foreground).
 */
export interface TreeZoomConfig {
    readonly horizonY: number;
    readonly foregroundY: number;
    readonly minWidth: number;
    readonly maxWidth: number;
    readonly steps: number;
}
/** Sprite definition with animations */
export interface SpriteConfig {
    readonly animations?: Record<string, SpriteAnimationConfig>;
    readonly source?: string;
    readonly widths?: readonly number[];
    readonly contrast?: number;
    readonly invert?: boolean;
    readonly zoom?: TreeZoomConfig;
    readonly layerConfig?: LayerSpriteConfig;
}
/** Behavior preset name */
export type LayerBehaviorPreset = keyof typeof LAYER_BEHAVIORS;
/** Layer definition from config */
export interface LayerDefinition {
    readonly name: string;
    readonly type?: LayerType;
    readonly sprites?: readonly string[];
    readonly positions?: readonly number[];
    readonly layer?: number;
    readonly tile?: boolean;
    readonly behavior?: LayerBehaviorPreset;
}
/**
 * Auto-layer generation configuration.
 *
 * Automatically generates tree layers spread across a depth range
 * with alternating sprites and randomized positions.
 *
 * sprites: Sprite names to alternate between layers.
 * minLayer: Nearest layer number (largest trees).
 * maxLayer: Farthest layer number (smallest trees).
 * treesPerLayer: Number of trees per layer (default 2).
 * seed: Random seed for consistent positions (default 12345).
 */
export interface AutoLayersConfig {
    readonly sprites: readonly string[];
    readonly minLayer: number;
    readonly maxLayer: number;
    readonly treesPerLayer?: number;
    readonly seed?: number;
}
/** Global settings */
export interface Settings {
    readonly fps: number;
    readonly jumpSpeed: number;
    readonly scrollSpeed: number;
}
/** Audio configuration (imported from audio module at runtime) */
export interface AudioConfigRef {
    readonly enabled: boolean;
    readonly masterVolume: number;
    readonly tracks: readonly {
        readonly id: string;
        readonly path: string;
        readonly volume: number;
        readonly loop: boolean;
        readonly tags: {
            readonly time?: "day" | "night" | "dawn" | "dusk";
            readonly location?: string;
        };
    }[];
}
/** Root config structure */
export interface Config {
    readonly sprites: Record<string, SpriteConfig>;
    readonly layers: readonly LayerDefinition[];
    readonly settings: Settings;
    readonly audio?: AudioConfigRef;
    readonly autoLayers?: AutoLayersConfig;
}
//# sourceMappingURL=types.d.ts.map