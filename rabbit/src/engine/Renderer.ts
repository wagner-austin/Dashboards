/**
 * Buffer-based ASCII renderer.
 * Handles drawing sprites to a character buffer and outputting to the DOM.
 */

import type { Sprite, Layer } from "../types.js";
import { getSizeKey } from "./Sprite.js";

export class Renderer {
  private readonly width: number;
  private readonly height: number;
  private readonly element: HTMLPreElement;
  // Flat buffer for predictable memory access - index = y * width + x
  private readonly buffer: string[];

  constructor(width: number, height: number, element: HTMLPreElement) {
    this.width = width;
    this.height = height;
    this.element = element;
    this.buffer = new Array<string>(width * height).fill(" ");
  }

  private getIndex(x: number, y: number): number {
    return y * this.width + x;
  }

  /** Clear the buffer to spaces */
  clear(): void {
    this.buffer.fill(" ");
  }

  /** Draw a sprite's current frame to the buffer */
  drawSprite(sprite: Sprite): void {
    const animation = sprite.animations.get(sprite.currentAnimation);
    if (animation === undefined) return;

    const hasMultipleDirections = animation.directions.length > 1;
    const key = getSizeKey(sprite.currentSize, sprite.direction, hasMultipleDirections);
    const frameSet = animation.sizes.get(key);
    if (frameSet === undefined) return;

    const frame = frameSet.frames[sprite.currentFrame];
    if (frame === undefined) return;

    const lines = frame.split("\n");
    for (const [dy, line] of lines.entries()) {
      for (let dx = 0; dx < line.length; dx++) {
        const char = line[dx];
        if (char === undefined || char === " ") continue;

        const x = Math.floor(sprite.x) + dx;
        const y = Math.floor(sprite.y) + dy;

        if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
          this.buffer[this.getIndex(x, y)] = char;
        }
      }
    }
  }

  /** Draw all sprites in a layer */
  drawLayer(layer: Layer): void {
    for (const sprite of layer.sprites) {
      this.drawSprite(sprite);
    }
  }

  /** Render the buffer to the DOM element */
  render(): void {
    let output = "";
    for (let y = 0; y < this.height; y++) {
      const start = y * this.width;
      const end = start + this.width;
      output += this.buffer.slice(start, end).join("") + "\n";
    }
    this.element.textContent = output;
  }

  /** Get buffer dimensions */
  getWidth(): number {
    return this.width;
  }

  getHeight(): number {
    return this.height;
  }
}
