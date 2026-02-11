/**
 * Layer system types.
 */
import type { FrameSet, LayerBehavior, LayerType } from "../types.js";
import type { Camera, DepthBounds } from "../world/Projection.js";
/**
 * Validated layer from config (after validation).
 *
 * name: Layer identifier.
 * type: Layer rendering type (static, tile, sprites).
 * layer: Discrete layer number (lower = closer, higher = farther).
 * spriteNames: Sprites contained in this layer.
 * positions: X world coordinates for sprite instances.
 * zIndex: Render order index.
 * tile: Whether sprites tile horizontally.
 * behavior: Layer behavior for parallax and wrapping.
 */
export interface ValidatedLayer {
    readonly name: string;
    readonly type: LayerType;
    readonly layer: number;
    readonly spriteNames: readonly string[];
    readonly positions: readonly number[];
    readonly zIndex: number;
    readonly tile: boolean;
    readonly behavior: LayerBehavior;
}
/**
 * Scene sprite state for generic scene objects.
 *
 * spriteName: Identifier for sprite lookup.
 * sizes: Available size variants.
 * sizeIdx: Current size index.
 * frameIdx: Current animation frame.
 * worldX: World X position.
 * worldZ: World Z position (depth).
 */
export interface SceneSpriteState {
    readonly spriteName: string;
    readonly sizes: readonly FrameSet[];
    sizeIdx: number;
    frameIdx: number;
    worldX: number;
    worldZ: number;
}
/**
 * Runtime layer with loaded entities.
 *
 * config: Validated layer configuration.
 * entities: Active sprite instances.
 */
export interface LayerInstance {
    readonly config: ValidatedLayer;
    readonly entities: SceneSpriteState[];
}
/**
 * Scene-wide state.
 *
 * layers: All active layer instances.
 * camera: Current camera position.
 * depthBounds: Bounds for depth wrapping (from config).
 */
export interface SceneState {
    readonly layers: readonly LayerInstance[];
    readonly depthBounds: DepthBounds;
    camera: Camera;
}
/**
 * Create initial scene state.
 *
 * Args:
 *     layers: Layer instances to include.
 *     camera: Initial camera position.
 *     depthBounds: Bounds for depth wrapping.
 *
 * Returns:
 *     SceneState with provided layers, camera, and depth bounds.
 */
export declare function createSceneState(layers: LayerInstance[], camera: Camera, depthBounds: DepthBounds): SceneState;
/**
 * Render candidate for depth-sorted rendering.
 *
 * Pairs an entity with an effective Z position for sorting.
 * Used to collect all render operations before sorting by depth.
 *
 * entity: The scene sprite to render.
 * effectiveZ: The world Z position to render at (may differ from entity.worldZ for wrapping).
 */
export interface RenderCandidate {
    readonly entity: SceneSpriteState;
    readonly effectiveZ: number;
}
/**
 * Create a render candidate.
 *
 * Args:
 *     entity: Scene sprite to render.
 *     effectiveZ: World Z position to render at.
 *
 * Returns:
 *     RenderCandidate with provided values.
 */
export declare function createRenderCandidate(entity: SceneSpriteState, effectiveZ: number): RenderCandidate;
//# sourceMappingURL=types.d.ts.map