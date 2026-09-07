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
import type { FrameSet } from "../types.js";
/** Module interface for sprite frame exports */
export interface SpriteModule {
    readonly frames: readonly string[];
}
/**
 * The calls that reach outside the process.
 *
 * A unit test cannot import over the network or fetch a file that is not
 * there, so these two are substitutable. Everything else in `io/` is not.
 */
export declare const _test_hooks: {
    importModule: (url: string) => Promise<unknown>;
    fetchFn: (url: string) => Promise<Response>;
    /** Drop every cached module, so one test's loads cannot serve another's. */
    clearSpriteModuleCache: () => void;
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
export declare function assetUrl(path: string): string;
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
export declare function importSpriteModule(path: string): Promise<SpriteModule>;
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
export declare function loadSpriteFrames(spriteName: string, animationName: string, width: number, direction?: string): Promise<FrameSet>;
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
export declare function loadStaticSpriteFrames(spriteName: string, width: number): Promise<FrameSet>;
//# sourceMappingURL=transport.d.ts.map