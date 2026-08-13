/**
 * Validation functions for autorun configuration.
 *
 * Kept free of engine imports so the config loader can validate an autorun
 * block without pulling in the input/entity modules.
 *
 * Every field is optional in config.json: omitted fields fall back to
 * DEFAULT_AUTORUN_CONFIG, so `{"enabled": true}` is a complete block.
 */
/** Default autorun configuration. */
export const DEFAULT_AUTORUN_CONFIG = {
    enabled: true,
    idleDelay: 5,
    minLeg: 2,
    maxLeg: 7,
    minPause: 3,
    maxPause: 9,
    turnChance: 0.5,
    hopChance: 0.25,
    jumpChance: 0.35,
};
/** Type guard for checking if value is a record */
function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}
/**
 * Require a boolean field, falling back to a default when absent.
 *
 * Args:
 *     value: Raw field value from config.
 *     field: Field name for error messages.
 *     fallback: Default used when the field is absent.
 *
 * Returns:
 *     The validated boolean.
 *
 * Raises:
 *     Error: If present but not a boolean.
 */
function requireBoolean(value, field, fallback) {
    if (value === undefined) {
        return fallback;
    }
    if (typeof value !== "boolean") {
        throw new Error(`autorun: "${field}" must be a boolean`);
    }
    return value;
}
/**
 * Require a numeric field within a range, falling back when absent.
 *
 * Args:
 *     value: Raw field value from config.
 *     field: Field name for error messages.
 *     fallback: Default used when the field is absent.
 *     min: Minimum allowed value (inclusive).
 *     max: Maximum allowed value (inclusive).
 *
 * Returns:
 *     The validated number.
 *
 * Raises:
 *     Error: If present but not a finite number within range.
 */
function requireNumber(value, field, fallback, min, max) {
    if (value === undefined) {
        return fallback;
    }
    if (typeof value !== "number" || !Number.isFinite(value) || value < min || value > max) {
        throw new Error(`autorun: "${field}" must be a number between ${String(min)} and ${String(max)}`);
    }
    return value;
}
/**
 * Validate an autorun configuration block from config.json.
 *
 * Absent blocks and absent fields fall back to DEFAULT_AUTORUN_CONFIG.
 *
 * Args:
 *     config: Raw autorun value from config.json, or undefined.
 *
 * Returns:
 *     Fully populated AutorunConfig.
 *
 * Raises:
 *     Error: If the block or any field has the wrong type or range.
 */
export function validateAutorunConfig(config) {
    if (config === undefined) {
        return DEFAULT_AUTORUN_CONFIG;
    }
    if (!isRecord(config)) {
        throw new Error("autorun: must be an object");
    }
    const defaults = DEFAULT_AUTORUN_CONFIG;
    const validated = {
        enabled: requireBoolean(config.enabled, "enabled", defaults.enabled),
        idleDelay: requireNumber(config.idleDelay, "idleDelay", defaults.idleDelay, 0, 3600),
        minLeg: requireNumber(config.minLeg, "minLeg", defaults.minLeg, 0, 3600),
        maxLeg: requireNumber(config.maxLeg, "maxLeg", defaults.maxLeg, 0, 3600),
        minPause: requireNumber(config.minPause, "minPause", defaults.minPause, 0, 3600),
        maxPause: requireNumber(config.maxPause, "maxPause", defaults.maxPause, 0, 3600),
        turnChance: requireNumber(config.turnChance, "turnChance", defaults.turnChance, 0, 1),
        hopChance: requireNumber(config.hopChance, "hopChance", defaults.hopChance, 0, 1),
        jumpChance: requireNumber(config.jumpChance, "jumpChance", defaults.jumpChance, 0, 1),
    };
    if (validated.minLeg > validated.maxLeg) {
        throw new Error('autorun: "minLeg" must not exceed "maxLeg"');
    }
    if (validated.minPause > validated.maxPause) {
        throw new Error('autorun: "minPause" must not exceed "maxPause"');
    }
    return validated;
}
/** Test hooks for internal functions */
export const _test_hooks = {
    isRecord,
    requireBoolean,
    requireNumber,
    validateAutorunConfig,
    DEFAULT_AUTORUN_CONFIG,
};
//# sourceMappingURL=validation.js.map