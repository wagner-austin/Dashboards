/**
 * Buffer-based ASCII renderer.
 * Handles drawing sprites to a character buffer and outputting to the DOM.
 */
import { getSizeKey } from "./Sprite.js";
export class Renderer {
    width;
    height;
    element;
    // Flat buffer for predictable memory access - index = y * width + x
    buffer;
    constructor(width, height, element) {
        this.width = width;
        this.height = height;
        this.element = element;
        this.buffer = new Array(width * height).fill(" ");
    }
    getIndex(x, y) {
        return y * this.width + x;
    }
    /** Clear the buffer to spaces */
    clear() {
        this.buffer.fill(" ");
    }
    /** Draw a sprite's current frame to the buffer */
    drawSprite(sprite) {
        const animation = sprite.animations.get(sprite.currentAnimation);
        if (animation === undefined)
            return;
        const hasMultipleDirections = animation.directions.length > 1;
        const key = getSizeKey(sprite.currentSize, sprite.direction, hasMultipleDirections);
        const frameSet = animation.sizes.get(key);
        if (frameSet === undefined)
            return;
        const frame = frameSet.frames[sprite.currentFrame];
        if (frame === undefined)
            return;
        const lines = frame.split("\n");
        for (const [dy, line] of lines.entries()) {
            for (let dx = 0; dx < line.length; dx++) {
                const char = line[dx];
                if (char === undefined || char === " ")
                    continue;
                const x = Math.floor(sprite.x) + dx;
                const y = Math.floor(sprite.y) + dy;
                if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
                    this.buffer[this.getIndex(x, y)] = char;
                }
            }
        }
    }
    /** Draw all sprites in a layer */
    drawLayer(layer) {
        for (const sprite of layer.sprites) {
            this.drawSprite(sprite);
        }
    }
    /** Render the buffer to the DOM element */
    render() {
        let output = "";
        for (let y = 0; y < this.height; y++) {
            const start = y * this.width;
            const end = start + this.width;
            output += this.buffer.slice(start, end).join("") + "\n";
        }
        this.element.textContent = output;
    }
    /** Get buffer dimensions */
    getWidth() {
        return this.width;
    }
    getHeight() {
        return this.height;
    }
}
//# sourceMappingURL=Renderer.js.map