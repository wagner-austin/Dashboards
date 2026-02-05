/**
 * Sprite drawing functions.
 */

export function drawSprite(
  buffer: string[][],
  lines: string[],
  x: number,
  y: number,
  width: number,
  height: number
): void {
  for (let i = 0; i < lines.length; i++) {
    const row = y + i;
    const line = lines[i];
    if (line === undefined) continue;
    if (row >= 0 && row < height) {
      for (let j = 0; j < line.length; j++) {
        const col = x + j;
        const ch = line[j];
        if (col >= 0 && col < width && ch !== undefined && ch !== " ") {
          const bufferRow = buffer[row];
          if (bufferRow !== undefined) {
            bufferRow[col] = ch;
          }
        }
      }
    }
  }
}

export function drawSpriteFade(
  buffer: string[][],
  oldLines: string[],
  newLines: string[],
  oldX: number,
  newX: number,
  oldY: number,
  newY: number,
  width: number,
  height: number,
  progress: number // 0 = all old, 1 = all new
): void {
  // Ease-in curve: prioritize showing new pixels sooner
  // progress^0.5 makes new pixels appear faster
  const easedProgress = Math.pow(progress, 0.5);

  // Draw new sprite first (fading in) - these take priority
  for (let i = 0; i < newLines.length; i++) {
    const row = newY + i;
    const line = newLines[i];
    if (line === undefined) continue;
    if (row >= 0 && row < height) {
      for (let j = 0; j < line.length; j++) {
        const col = newX + j;
        const ch = line[j];
        if (col >= 0 && col < width && ch !== undefined && ch !== " ") {
          // Higher chance to show new pixels (eased progress)
          if (Math.random() < easedProgress) {
            const bufferRow = buffer[row];
            if (bufferRow !== undefined) {
              bufferRow[col] = ch;
            }
          }
        }
      }
    }
  }

  // Draw old sprite (fading out) - only fills gaps
  const inverseEased = 1 - easedProgress;
  for (let i = 0; i < oldLines.length; i++) {
    const row = oldY + i;
    const line = oldLines[i];
    if (line === undefined) continue;
    if (row < 0 || row >= height) continue;
    const bufferRow = buffer[row];
    if (bufferRow === undefined) continue;
    for (let j = 0; j < line.length; j++) {
      const col = oldX + j;
      const ch = line[j];
      if (
        col >= 0 &&
        col < width &&
        ch !== undefined &&
        ch !== " " &&
        bufferRow[col] === " " &&
        Math.random() < inverseEased
      ) {
        bufferRow[col] = ch;
      }
    }
  }
}
