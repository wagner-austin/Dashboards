/**
 * Math utilities for animations and transitions.
 */
/** Speed multiplier calculation for a given tree size index */
export declare function getSpeedMultiplier(treeSizeIdx: number): number;
/** Ease-in-out S-curve for smooth transitions */
export declare function easeInOut(progress: number): number;
/** Lerp between two values with optional easing */
export declare function lerp(start: number, end: number, progress: number, eased?: boolean): number;
//# sourceMappingURL=math.d.ts.map