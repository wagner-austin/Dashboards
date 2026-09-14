/** Local perception for the rabbit: trees, companion distance, and exploration. */
import type { SceneState } from "../layers/types.js";
import type { CompanionState } from "../entities/Companion.js";
import { WORLD_WIDTH } from "../world/Projection.js";
import type { HorizontalDirection } from "./intent.js";

export interface Awareness {
  readonly wait: boolean;
  readonly blocked: boolean;
  readonly direction: HorizontalDirection;
}

/** Nearest periodic image, including arbitrary multi-world travel. */
export function wrappedDelta(delta: number, range: number): number {
  return range > 0 ? ((delta + range / 2) % range + range) % range - range / 2 : delta;
}

export function senseWorld(
  scene: SceneState, companion: CompanionState | null, facingRight: boolean
): Awareness {
  const direction = facingRight ? 1 : -1;
  let blocked = false;
  for (const layer of scene.layers) {
    if (layer.config.tile || layer.config.type === "static") continue;
    for (const tree of layer.entities) {
      const dx = wrappedDelta(tree.worldX - scene.camera.x, WORLD_WIDTH);
      const dz = wrappedDelta(tree.worldZ - scene.camera.z - 40, scene.depthBounds.range);
      if (Math.abs(dz) < 13 && dx * direction > 0 && dx * direction < 65) blocked = true;
    }
  }
  return {
    wait: companion !== null && Math.hypot(companion.x, companion.z) > 225,
    blocked,
    direction: blocked ? (facingRight ? "left" : "right") : (facingRight ? "right" : "left"),
  };
}

export const _test_hooks = { wrappedDelta, senseWorld };
