/**
 * Ground tile rendering.
 */

export const GROUND_TILE = [
  "                                                            ",
  "      .                  .                .                 ",
  "  .       .      +           .       .          .     +     ",
  "     .        .      .   +       .        .  +      .    .  ",
  " .      + .      .  .      . .      +  .      .   .     .   ",
  "   . .     .  +    .   . .    .  .     . +     . .   +   .  ",
];

export function drawGround(
  buffer: string[][],
  offsetX: number,
  width: number,
  height: number
): void {
  const tileWidth = GROUND_TILE[0]?.length ?? 60;
  for (let i = 0; i < GROUND_TILE.length; i++) {
    const row = height - GROUND_TILE.length + i;
    const tileLine = GROUND_TILE[i];
    if (row >= 0 && row < height && tileLine !== undefined) {
      const bufferRow = buffer[row];
      if (bufferRow === undefined) continue;
      for (let col = 0; col < width; col++) {
        const srcCol =
          ((col - Math.floor(offsetX)) % tileWidth + tileWidth) % tileWidth;
        const ch = tileLine[srcCol];
        if (ch !== undefined && ch !== " ") {
          bufferRow[col] = ch;
        }
      }
    }
  }
}
