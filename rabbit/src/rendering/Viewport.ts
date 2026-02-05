/**
 * Viewport measurement and buffer management.
 */

export interface ViewportState {
  width: number;
  height: number;
  charW: number;
  charH: number;
}

export function measureViewport(screen: HTMLPreElement): ViewportState {
  const vw = document.documentElement.clientWidth;
  const vh = document.documentElement.clientHeight;

  // Measure actual character size
  screen.textContent = "X";
  const rect = screen.getBoundingClientRect();
  const charW = rect.width;
  const charH = rect.height;
  screen.textContent = "";

  return {
    width: Math.floor(vw / charW),
    height: Math.floor(vh / charH),
    charW,
    charH,
  };
}

export function createBuffer(width: number, height: number): string[][] {
  return Array.from({ length: height }, () => Array(width).fill(" ") as string[]);
}

export function renderBuffer(buffer: string[][]): string {
  return buffer.map((row) => row.join("")).join("\n");
}
