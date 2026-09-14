/** Local perception for the rabbit: trees, companion distance, and exploration. */
import type { SceneState } from "../layers/types.js";
import type { CompanionState } from "../entities/Companion.js";
import type { HorizontalDirection } from "./intent.js";
export interface Awareness {
    readonly wait: boolean;
    readonly blocked: boolean;
    readonly direction: HorizontalDirection;
}
/** Nearest periodic image, including arbitrary multi-world travel. */
export declare function wrappedDelta(delta: number, range: number): number;
export declare function senseWorld(scene: SceneState, companion: CompanionState | null, facingRight: boolean): Awareness;
export declare const _test_hooks: {
    wrappedDelta: typeof wrappedDelta;
    senseWorld: typeof senseWorld;
};
//# sourceMappingURL=Awareness.d.ts.map