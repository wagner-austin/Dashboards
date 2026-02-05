/**
 * Ground tile rendering.
 */
export declare const GROUND_TILE: readonly ["                                                            ", "      .                  .                .                 ", "  .       .      +           .       .          .     +     ", "     .        .      .   +       .        .  +      .    .  ", " .      + .      .  .      . .      +  .      .   .     .   ", "   . .     .  +    .   . .    .  .     . +     . .   +   .  "];
/** Width of each ground tile row - computed from first row at module load */
export declare const GROUND_TILE_WIDTH: number;
export declare function drawGround(buffer: string[][], offsetX: number, width: number, height: number): void;
//# sourceMappingURL=Ground.d.ts.map