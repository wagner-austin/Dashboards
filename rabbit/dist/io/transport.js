/**
 * The boundary between this program and everything outside it.
 *
 * Two calls leave the process: a dynamic `import()` of a sprite module and a
 * `fetch` of config.json. Both live here, behind seams, so that the modules
 * built on top of them — character assembly, scene loading, load ordering —
 * are ordinary testable logic rather than code that happens to sit next to a
 * network call.
 *
 * Nothing here knows what a character or a tree is. It resolves a path to a
 * URL, imports it once, and validates the shape that comes back.
 */
import { _test_hooks as spritesHooks } from "../loaders/sprites.js";
const { validateSpriteModule } = spritesHooks;
/** Cache bust version timestamp - updated on each build. */
const CACHE_VERSION = Date.now();
/** Cache for loaded sprite modules to prevent duplicate downloads */
const spriteModuleCache = new Map();
/**
 * The calls that reach outside the process.
 *
 * A unit test cannot import over the network or fetch a file that is not
 * there, so these two are substitutable. Everything else in `io/` is not.
 */
export const _test_hooks = {
    importModule: (url) => import(/* @vite-ignore */ url),
    fetchFn: (url) => fetch(url),
    /** Drop every cached module, so one test's loads cannot serve another's. */
    clearSpriteModuleCache: () => {
        spriteModuleCache.clear();
    },
};
/**
 * Resolve an asset path against the PAGE, not against this module.
 *
 * A relative specifier passed to dynamic `import()` resolves against the
 * importing module's URL, which makes sprite loading depend on where the
 * built JavaScript happens to sit. Bundling moved this code from `dist/io/`
 * to `bundle/`, and every sprite 404'd because `../sprites/` silently started
 * resolving one directory higher.
 *
 * Anchoring to `document.baseURI` removes that coupling: the sprites live at
 * a fixed place relative to the page, so the bundle can be emitted anywhere.
 *
 * Args:
 *     path: Path relative to the page, e.g. `dist/sprites/tree1/w40.js`.
 *
 * Returns:
 *     Absolute URL string for the module, carrying the cache-bust query.
 */
export function assetUrl(path) {
    return new URL(`${path}?v=${String(CACHE_VERSION)}`, document.baseURI).href;
}
/**
 * Import a sprite module once, validating what comes back.
 *
 * The promise is cached before it resolves, so callers arriving while an
 * import is still in flight join it rather than starting a second download.
 *
 * Args:
 *     path: Page-relative module path.
 *
 * Returns:
 *     The validated module.
 *
 * Raises:
 *     Error: If the module does not export a string array named `frames`.
 */
export async function importSpriteModule(path) {
    const cached = spriteModuleCache.get(path);
    if (cached !== undefined) {
        return cached;
    }
    const promise = (async () => {
        const module = await _test_hooks.importModule(assetUrl(path));
        return validateSpriteModule(module, path);
    })();
    spriteModuleCache.set(path, promise);
    return promise;
}
/**
 * Load one animation's frames at a width, optionally direction-suffixed.
 *
 * Args:
 *     spriteName: Sprite directory name.
 *     animationName: Animation directory name.
 *     width: Character width.
 *     direction: "left" or "right", or omitted for an undirected sprite.
 *
 * Returns:
 *     The frame set at that width.
 */
export async function loadSpriteFrames(spriteName, animationName, width, direction) {
    const suffix = direction !== undefined ? `_${direction}` : "";
    const path = `dist/sprites/${spriteName}/${animationName}/w${String(width)}${suffix}.js`;
    const module = await importSpriteModule(path);
    return { width, frames: module.frames };
}
/**
 * Load a static sprite's frames at a width.
 *
 * Args:
 *     spriteName: Sprite directory name.
 *     width: Character width.
 *
 * Returns:
 *     The frame set at that width.
 */
export async function loadStaticSpriteFrames(spriteName, width) {
    const path = `dist/sprites/${spriteName}/w${String(width)}.js`;
    const module = await importSpriteModule(path);
    return { width, frames: module.frames };
}
//# sourceMappingURL=transport.js.map