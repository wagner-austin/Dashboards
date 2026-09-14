/** Companion movement and attentive idle poses, independent of browser I/O. */
import { createCompanion, stepCompanion } from "./Companion.js";
import { wrappedDelta } from "../input/Awareness.js";
/**
 * Create an independently clocked companion and idle-pose service.
 *
 * Args:
 *   assets: Validated animation sequences, already loaded.
 *   leader: Selected character name.
 *   initialCamera: Starting camera used to measure real displacement.
 *   depthRange: Period of the world's depth wrapping.
 * Returns:
 *   A focused service producing immutable render snapshots.
 */
export function createAdventure(assets, leader, initialCamera, depthRange) {
    let companion = createCompanion();
    let previousCamera = initialCamera;
    let idleSeconds = 0;
    let sprintSeconds = 0;
    return {
        update(dt, camera, bunny, sprinting) {
            const cameraDx = camera.x - previousCamera.x;
            // R resets and depth wrapping are coordinate changes, not a sprint across the world.
            const reset = Math.abs(cameraDx) > 300;
            companion = stepCompanion(reset ? createCompanion() : companion, {
                deltaTime: dt,
                cameraDx: reset ? 0 : cameraDx,
                cameraDz: wrappedDelta(camera.z - previousCamera.z, depthRange),
                facingRight: bunny.facingRight,
                jumping: bunny.animation.kind === "jump",
            });
            previousCamera = camera;
            idleSeconds = bunny.animation.kind === "idle" ? idleSeconds + dt : 0;
            let alert = null;
            sprintSeconds = sprinting ? sprintSeconds + dt : 0;
            if (leader === "lion" && sprinting && bunny.animation.kind === "walk") {
                const sequence = bunny.facingRight ? assets.lionSprint.right : assets.lionSprint.left;
                const frame = sequence[Math.floor(sprintSeconds / 0.075) % sequence.length];
                if (frame === undefined)
                    throw new Error("RABBIT_SPRINT_FRAME: Sprint animation is empty.");
                alert = frame.split("\n");
            }
            if (leader === "bunny" && idleSeconds >= 0.65) {
                const sequence = bunny.facingRight ? assets.alertRight : assets.alertLeft;
                const index = Math.min(sequence.length - 1, Math.floor((idleSeconds - 0.65) / 0.3));
                const frame = sequence[index];
                if (frame === undefined)
                    throw new Error("RABBIT_ALERT_FRAME: Upright animation is empty.");
                alert = frame.split("\n");
            }
            return { companion, assets, alert,
                companionSprint: leader === "bunny" ? assets.lionSprint : { left: assets.companion.walkLeft, right: assets.companion.walkRight },
                companionColor: leader === "bunny" ? "#58baff" : "#ffffff",
                status: leader === "bunny" && alert !== null ? "Rabbit is looking around" : companion.mode === "jump"
                    ? "Jumping together" : companion.mode === "run" ? "Companion is catching up" : "Exploring together" };
        },
    };
}
export const _test_hooks = { createAdventure };
//# sourceMappingURL=Adventure.js.map