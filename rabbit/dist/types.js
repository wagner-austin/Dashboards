/**
 * Core type definitions for the ASCII animation engine.
 */
/**
 * Preset layer behaviors for common layer types.
 */
export const LAYER_BEHAVIORS = {
    /** Sky/background - fixed, no wrapping */
    static: { parallax: 0, wrapX: false, wrapZ: false },
    /** Distant mountains - slow parallax, no wrapping */
    background: { parallax: 0.3, wrapX: false, wrapZ: false },
    /** Trees/objects - full tracking, X wrap for infinite scroll */
    midground: { parallax: 1.0, wrapX: true, wrapZ: false },
    /** Ground plane - full tracking, X wrap, tiles horizontally */
    foreground: { parallax: 1.0, wrapX: true, wrapZ: false },
};
//# sourceMappingURL=types.js.map