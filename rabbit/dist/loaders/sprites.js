/**
 * Sprite loading and animation timer utilities.
 */
export async function loadSpriteFrames(spriteName, animationName, width, direction) {
    const suffix = direction !== undefined ? `_${direction}` : "";
    const module = (await import(`../sprites/${spriteName}/${animationName}/w${String(width)}${suffix}.js`));
    return {
        width,
        frames: module.frames,
    };
}
export async function loadStaticSpriteFrames(spriteName, width) {
    const module = (await import(`../sprites/${spriteName}/w${String(width)}.js`));
    return {
        width,
        frames: module.frames,
    };
}
export async function loadConfig() {
    const response = await fetch("./config.json");
    return (await response.json());
}
export function createAnimationTimer(intervalMs, onTick) {
    let id = null;
    return {
        start() {
            if (id !== null)
                return;
            id = setInterval(onTick, intervalMs);
        },
        stop() {
            if (id !== null) {
                clearInterval(id);
                id = null;
            }
        },
        isRunning() {
            return id !== null;
        },
    };
}
//# sourceMappingURL=sprites.js.map