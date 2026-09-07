/**
 * Validation for the render layer colour block.
 *
 * The scene is drawn into three stacked <pre> elements rather than one, so
 * that the actor can carry its own colour without the renderer having to
 * track a colour per character cell. Each element gets a CSS colour from
 * here.
 *
 * Kept free of engine imports, like input/validation.ts, so the config loader
 * can validate a colours block without pulling in the rendering modules.
 *
 * Every field is optional in config.json: omitted fields fall back to
 * DEFAULT_LAYER_COLORS, so `{"actor": "#6db3ff"}` is a complete block and
 * leaves the world exactly as it was.
 */
/**
 * Default layer colours.
 *
 * All three match the single colour the page used when the scene rendered
 * into one element, so a config with no colours block is pixel-identical to
 * the pre-split engine.
 */
export const DEFAULT_LAYER_COLORS = {
    world: "#e0e0e0",
    actor: "#e0e0e0",
    foreground: "#e0e0e0",
};
/** Type guard for checking if value is a record */
function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}
/**
 * Require a CSS colour field, falling back to a default when absent.
 *
 * The value is checked for being a non-empty string and nothing more. CSS
 * colour syntax is large (hex, rgb(), hsl(), named colours) and the browser
 * is the authority on it; re-implementing a partial parser here would reject
 * valid colours, which is worse than passing an invalid one through to a
 * declaration the browser ignores.
 *
 * Args:
 *     value: Raw field value from config.
 *     field: Field name for error messages.
 *     fallback: Default used when the field is absent.
 *
 * Returns:
 *     The validated colour string.
 *
 * Raises:
 *     Error: If present but not a non-empty string.
 */
function requireColor(value, field, fallback) {
    if (value === undefined) {
        return fallback;
    }
    if (typeof value !== "string" || value.trim() === "") {
        throw new Error(`colors: "${field}" must be a non-empty string`);
    }
    return value;
}
/**
 * Validate a colours block from config.json.
 *
 * Absent blocks and absent fields fall back to DEFAULT_LAYER_COLORS.
 *
 * Args:
 *     config: Raw colors value from config.json, or undefined.
 *
 * Returns:
 *     Fully populated LayerColors.
 *
 * Raises:
 *     Error: If the block or any field has the wrong type.
 */
export function validateColorsConfig(config) {
    if (config === undefined) {
        return DEFAULT_LAYER_COLORS;
    }
    if (!isRecord(config)) {
        throw new Error("colors: must be an object");
    }
    const defaults = DEFAULT_LAYER_COLORS;
    return {
        world: requireColor(config.world, "world", defaults.world),
        actor: requireColor(config.actor, "actor", defaults.actor),
        foreground: requireColor(config.foreground, "foreground", defaults.foreground),
    };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    isRecord,
    requireColor,
    validateColorsConfig,
    DEFAULT_LAYER_COLORS,
};
//# sourceMappingURL=colors.js.map