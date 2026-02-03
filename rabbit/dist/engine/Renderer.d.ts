/**
 * Buffer-based ASCII renderer.
 * Handles drawing sprites to a character buffer and outputting to the DOM.
 */
import type { Sprite, Layer } from "../types.js";
export declare class Renderer {
    private readonly width;
    private readonly height;
    private readonly element;
    private readonly buffer;
    constructor(width: number, height: number, element: HTMLPreElement);
    private getIndex;
    /** Clear the buffer to spaces */
    clear(): void;
    /** Draw a sprite's current frame to the buffer */
    drawSprite(sprite: Sprite): void;
    /** Draw all sprites in a layer */
    drawLayer(layer: Layer): void;
    /** Render the buffer to the DOM element */
    render(): void;
    /** Get buffer dimensions */
    getWidth(): number;
    getHeight(): number;
}
//# sourceMappingURL=Renderer.d.ts.map