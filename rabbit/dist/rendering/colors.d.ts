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
 * CSS colours for the three stacked render layers.
 *
 * world: Trees, ground, and everything behind the actor.
 * actor: The character. The only layer that normally differs.
 * foreground: Grass and anything drawn in front of the actor.
 */
export interface LayerColors {
    readonly world: string;
    readonly actor: string;
    readonly foreground: string;
}
/**
 * Default layer colours.
 *
 * All three match the single colour the page used when the scene rendered
 * into one element, so a config with no colours block is pixel-identical to
 * the pre-split engine.
 */
export declare const DEFAULT_LAYER_COLORS: LayerColors;
/** Type guard for checking if value is a record */
declare function isRecord(value: unknown): value is Record<string, unknown>;
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
declare function requireColor(value: unknown, field: string, fallback: string): string;
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
export declare function validateColorsConfig(config: unknown): LayerColors;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    isRecord: typeof isRecord;
    requireColor: typeof requireColor;
    validateColorsConfig: typeof validateColorsConfig;
    DEFAULT_LAYER_COLORS: LayerColors;
};
export {};
//# sourceMappingURL=colors.d.ts.map