/**
 * Sprite drawing functions.
 */
/** Density level type (0-5). Space (invisible) is handled by early return. */
type DensityLevel = 0 | 1 | 2 | 3 | 4 | 5;
/**
 * Convert density level to character.
 *
 * Args:
 *     level: Density level from 0 (densest) to 5 (lightest visible).
 *
 * Returns:
 *     Character at that density level.
 */
declare function densityToChar(level: DensityLevel): string;
/**
 * Clamp a number to a valid density level.
 *
 * Args:
 *     n: Number to clamp.
 *
 * Returns:
 *     DensityLevel between 0 and 5.
 */
declare function clampToDensity(n: number): DensityLevel;
/**
 * Get a faded version of a character based on visibility.
 *
 * Maps the character to a density level and fades toward empty space.
 * Characters not in CHAR_DENSITY are treated as maximum density (0).
 *
 * Args:
 *     ch: Input character to fade.
 *     visibility: Visibility level from 0 (invisible) to 1 (fully visible).
 *
 * Returns:
 *     Faded character from the density gradient.
 */
declare function getFadedChar(ch: string, visibility: number): string;
export declare function drawSprite(buffer: string[][], lines: string[], x: number, y: number, width: number, height: number): void;
/**
 * Sample a character from sprite at normalized coordinates.
 * Coordinates are relative to bottom-center anchor (0,0 = center-bottom).
 */
declare function sampleSprite(lines: string[], spriteWidth: number, normX: number, // -0.5 to 0.5 (left to right)
normY: number): string | undefined;
export declare function drawSpriteFade(buffer: string[][], oldLines: string[], newLines: string[], oldCenterX: number, oldCenterY: number, newCenterX: number, newCenterY: number, oldWidth: number, newWidth: number, width: number, height: number, progress: number, // 0 = all old, 1 = all new
visibility?: number): void;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    densityToChar: typeof densityToChar;
    clampToDensity: typeof clampToDensity;
    getFadedChar: typeof getFadedChar;
    drawSprite: typeof drawSprite;
    sampleSprite: typeof sampleSprite;
    drawSpriteFade: typeof drawSpriteFade;
};
export {};
//# sourceMappingURL=draw.d.ts.map