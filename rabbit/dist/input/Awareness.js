import { WORLD_WIDTH } from "../world/Projection.js";
/** Nearest periodic image, including arbitrary multi-world travel. */
export function wrappedDelta(delta, range) {
    return range > 0 ? ((delta + range / 2) % range + range) % range - range / 2 : delta;
}
export function senseWorld(scene, companion, facingRight) {
    const direction = facingRight ? 1 : -1;
    let blocked = false;
    for (const layer of scene.layers) {
        if (layer.config.tile || layer.config.type === "static")
            continue;
        for (const tree of layer.entities) {
            const dx = wrappedDelta(tree.worldX - scene.camera.x, WORLD_WIDTH);
            const dz = wrappedDelta(tree.worldZ - scene.camera.z - 40, scene.depthBounds.range);
            if (Math.abs(dz) < 13 && dx * direction > 0 && dx * direction < 65)
                blocked = true;
        }
    }
    return {
        wait: companion !== null && Math.hypot(companion.x, companion.z) > 225,
        blocked,
        direction: blocked ? (facingRight ? "left" : "right") : (facingRight ? "right" : "left"),
    };
}
export const _test_hooks = { wrappedDelta, senseWorld };
//# sourceMappingURL=Awareness.js.map