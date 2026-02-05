/**
 * Layer system types.
 */
import type { FrameSet, LayerType } from "../types.js";
/** Validated layer from config (after validation) */
export interface ValidatedLayer {
    readonly name: string;
    readonly type: LayerType;
    readonly parallax: number;
    readonly spriteNames: readonly string[];
    readonly zIndex: number;
    readonly tile: boolean;
}
/** Scene sprite state for generic scene objects */
export interface SceneSpriteState {
    readonly spriteName: string;
    readonly sizes: readonly FrameSet[];
    sizeIdx: number;
    frameIdx: number;
    x: number;
}
/** Runtime layer with loaded entities */
export interface LayerInstance {
    readonly config: ValidatedLayer;
    readonly entities: SceneSpriteState[];
}
/** Scene-wide state */
export interface SceneState {
    readonly layers: readonly LayerInstance[];
    cameraX: number;
}
/** Create initial scene state */
export declare function createSceneState(layers: LayerInstance[]): SceneState;
//# sourceMappingURL=types.d.ts.map