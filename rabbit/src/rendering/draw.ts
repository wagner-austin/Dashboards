/**
 * Sprite drawing functions.
 */

/** Character density levels for smooth fade (0 = densest, 5 = lightest). */
const CHAR_DENSITY: Record<string, number> = {
  "#": 0, "+": 1, "=": 2, "-": 3, ":": 4, ".": 5,
};

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
function densityToChar(level: DensityLevel): string {
  switch (level) {
    case 0: return "#";
    case 1: return "+";
    case 2: return "=";
    case 3: return "-";
    case 4: return ":";
    case 5: return ".";
  }
}

/**
 * Clamp a number to a valid density level.
 *
 * Args:
 *     n: Number to clamp.
 *
 * Returns:
 *     DensityLevel between 0 and 5.
 */
function clampToDensity(n: number): DensityLevel {
  if (n <= 0) return 0;
  if (n >= 5) return 5;
  if (n >= 4) return 4;
  if (n >= 3) return 3;
  if (n >= 2) return 2;
  return 1;
}

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
function getFadedChar(ch: string, visibility: number): string {
  if (visibility >= 1) return ch;

  // Characters not in CHAR_DENSITY are treated as maximum density (0)
  const startLevel = CHAR_DENSITY[ch] ?? 0;
  const fadeSteps = 5 - startLevel;
  const fadeAmount = Math.floor((1 - visibility) * fadeSteps);
  const resultLevel = clampToDensity(startLevel + fadeAmount);

  return densityToChar(resultLevel);
}

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

/**
 * Sample a character from sprite at normalized coordinates.
 * Coordinates are relative to bottom-center anchor (0,0 = center-bottom).
 */
function sampleSprite(
  lines: string[],
  spriteWidth: number,
  normX: number, // -0.5 to 0.5 (left to right)
  normY: number  // -1 to 0 (top to bottom)
): string | undefined {
  const spriteHeight = lines.length;
  // Convert normalized coords to sprite-local coords (floor for consistency)
  const localX = Math.floor((normX + 0.5) * spriteWidth);
  const localY = Math.floor((normY + 1) * spriteHeight);

  if (localY < 0 || localY >= spriteHeight) return undefined;
  if (localX < 0 || localX >= spriteWidth) return undefined;

  const line = lines[localY];
  if (line === undefined) return undefined;

  const ch = line[localX];
  return ch === " " ? undefined : ch;
}

export function drawSpriteFade(
  buffer: string[][],
  oldLines: string[],
  newLines: string[],
  oldCenterX: number,
  oldCenterY: number,
  newCenterX: number,
  newCenterY: number,
  oldWidth: number,
  newWidth: number,
  width: number,
  height: number,
  progress: number, // 0 = all old, 1 = all new
  visibility = 1 // 0 = fully hidden, 1 = fully visible
): void {
  if (visibility <= 0) return;

  // Smooth ease-in-out to reduce jitter
  const easedProgress = progress < 0.5
    ? 2 * progress * progress
    : 1 - Math.pow(-2 * progress + 2, 2) / 2;

  // Keep floating point for smooth lerp, only floor when drawing
  const centerXf = oldCenterX + (newCenterX - oldCenterX) * easedProgress;
  const centerYf = oldCenterY + (newCenterY - oldCenterY) * easedProgress;
  const lerpWidthF = oldWidth + (newWidth - oldWidth) * easedProgress;
  const lerpHeightF = oldLines.length + (newLines.length - oldLines.length) * easedProgress;

  // Use floor consistently to avoid oscillation between rounded values
  const centerX = Math.floor(centerXf);
  const centerY = Math.floor(centerYf);
  const lerpWidth = Math.max(1, Math.floor(lerpWidthF));
  const lerpHeight = Math.max(1, Math.floor(lerpHeightF));

  // Draw at lerped position/size
  const drawX = centerX - Math.floor(lerpWidth / 2);
  const drawY = centerY - lerpHeight;

  // Max distance for transition ordering (from center-bottom)
  const maxDist = Math.sqrt(lerpWidth * lerpWidth / 4 + lerpHeight * lerpHeight);

  for (let i = 0; i < lerpHeight; i++) {
    const row = drawY + i;
    if (row < 0 || row >= height) continue;

    const bufferRow = buffer[row];
    if (bufferRow === undefined) continue;

    for (let j = 0; j < lerpWidth; j++) {
      const col = drawX + j;
      if (col < 0 || col >= width) continue;

      // Normalized coords relative to bottom-center (-0.5 to 0.5 X, -1 to 0 Y)
      const normX = (j / lerpWidth) - 0.5;
      const normY = (i / lerpHeight) - 1;

      // Sample both sprites at this normalized position
      const oldCh = sampleSprite(oldLines, oldWidth, normX, normY);
      const newCh = sampleSprite(newLines, newWidth, normX, normY);

      // If same character at same normalized position, draw solid - no transition
      if (oldCh !== undefined && oldCh === newCh) {
        bufferRow[col] = getFadedChar(oldCh, visibility);
        continue;
      }

      // Different characters - transition based on distance from center
      const dx = j - lerpWidth / 2;
      const dy = i - lerpHeight; // Distance from bottom
      const dist = Math.sqrt(dx * dx + dy * dy);
      // maxDist is guaranteed > 0 since lerpWidth >= 1 and lerpHeight >= 1
      const normalizedDist = Math.min(dist / maxDist, 1);

      // Edges change first (low threshold), center changes last (high threshold)
      // Scale to 0.01-0.99 to ensure progress 0 shows all old, progress 1 shows all new
      const threshold = 0.99 - normalizedDist * 0.98;

      let charToDraw: string | undefined;
      if (easedProgress > threshold) {
        charToDraw = newCh;
      } else {
        charToDraw = oldCh;
      }

      if (charToDraw !== undefined) {
        bufferRow[col] = getFadedChar(charToDraw, visibility);
      }
    }
  }
}
