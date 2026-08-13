/**
 * Validation functions for autorun configuration.
 *
 * Kept free of engine imports so the config loader can validate an autorun
 * block without pulling in the input/entity modules.
 *
 * Every field is optional in config.json: omitted fields fall back to
 * DEFAULT_AUTORUN_CONFIG, so `{"enabled": true}` is a complete block.
 */
/**
 * Autorun (idle autopilot) configuration.
 *
 * enabled: Whether the autopilot may engage at all.
 * idleDelay: Seconds of no user input before the autopilot takes over.
 * minLeg: Shortest movement leg (walk or hop) in seconds.
 * maxLeg: Longest movement leg in seconds.
 * minPause: Shortest idle pause between legs in seconds.
 * maxPause: Longest idle pause between legs in seconds.
 * turnChance: Probability (0-1) a new walk leg reverses direction.
 * hopChance: Probability (0-1) a leg is a depth hop instead of a walk.
 * jumpChance: Probability (0-1) a walk leg ends with a jump.
 */
export interface AutorunConfig {
    readonly enabled: boolean;
    readonly idleDelay: number;
    readonly minLeg: number;
    readonly maxLeg: number;
    readonly minPause: number;
    readonly maxPause: number;
    readonly turnChance: number;
    readonly hopChance: number;
    readonly jumpChance: number;
}
/** Default autorun configuration. */
export declare const DEFAULT_AUTORUN_CONFIG: AutorunConfig;
/** Type guard for checking if value is a record */
declare function isRecord(value: unknown): value is Record<string, unknown>;
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
declare function requireBoolean(value: unknown, field: string, fallback: boolean): boolean;
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
declare function requireNumber(value: unknown, field: string, fallback: number, min: number, max: number): number;
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
export declare function validateAutorunConfig(config: unknown): AutorunConfig;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    isRecord: typeof isRecord;
    requireBoolean: typeof requireBoolean;
    requireNumber: typeof requireNumber;
    validateAutorunConfig: typeof validateAutorunConfig;
    DEFAULT_AUTORUN_CONFIG: AutorunConfig;
};
export {};
//# sourceMappingURL=validation.d.ts.map