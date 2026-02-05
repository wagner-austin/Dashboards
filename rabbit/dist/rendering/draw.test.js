/**
 * Tests for sprite drawing functions.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { drawSprite, drawSpriteFade } from "./draw.js";
function createBuffer(width, height) {
    return Array.from({ length: height }, () => Array(width).fill(" "));
}
function bufferToString(buffer) {
    return buffer.map((row) => row.join("")).join("\n");
}
function getCell(buffer, row, col) {
    const r = buffer[row];
    if (r === undefined)
        throw new Error(`Row ${String(row)} not found`);
    const c = r[col];
    if (c === undefined)
        throw new Error(`Col ${String(col)} not found`);
    return c;
}
function setCell(buffer, row, col, value) {
    const r = buffer[row];
    if (r === undefined)
        throw new Error(`Row ${String(row)} not found`);
    r[col] = value;
}
describe("drawSprite", () => {
    it("draws sprite at specified position", () => {
        const buffer = createBuffer(10, 5);
        const sprite = ["AB", "CD"];
        drawSprite(buffer, sprite, 2, 1, 10, 5);
        expect(getCell(buffer, 1, 2)).toBe("A");
        expect(getCell(buffer, 1, 3)).toBe("B");
        expect(getCell(buffer, 2, 2)).toBe("C");
        expect(getCell(buffer, 2, 3)).toBe("D");
    });
    it("clips sprite at left edge", () => {
        const buffer = createBuffer(10, 5);
        const sprite = ["ABC"];
        drawSprite(buffer, sprite, -1, 0, 10, 5);
        expect(getCell(buffer, 0, 0)).toBe("B");
        expect(getCell(buffer, 0, 1)).toBe("C");
    });
    it("clips sprite at right edge", () => {
        const buffer = createBuffer(10, 5);
        const sprite = ["ABC"];
        drawSprite(buffer, sprite, 8, 0, 10, 5);
        expect(getCell(buffer, 0, 8)).toBe("A");
        expect(getCell(buffer, 0, 9)).toBe("B");
    });
    it("clips sprite at top edge", () => {
        const buffer = createBuffer(10, 5);
        const sprite = ["A", "B", "C"];
        drawSprite(buffer, sprite, 0, -1, 10, 5);
        expect(getCell(buffer, 0, 0)).toBe("B");
        expect(getCell(buffer, 1, 0)).toBe("C");
    });
    it("clips sprite at bottom edge", () => {
        const buffer = createBuffer(10, 5);
        const sprite = ["A", "B", "C"];
        drawSprite(buffer, sprite, 0, 3, 10, 5);
        expect(getCell(buffer, 3, 0)).toBe("A");
        expect(getCell(buffer, 4, 0)).toBe("B");
    });
    it("does not overwrite with spaces", () => {
        const buffer = createBuffer(10, 5);
        setCell(buffer, 0, 0, "X");
        const sprite = [" "];
        drawSprite(buffer, sprite, 0, 0, 10, 5);
        expect(getCell(buffer, 0, 0)).toBe("X");
    });
    it("handles empty sprite", () => {
        const buffer = createBuffer(10, 5);
        drawSprite(buffer, [], 0, 0, 10, 5);
        // Should not throw, buffer unchanged
        expect(bufferToString(buffer)).toBe("          \n          \n          \n          \n          ");
    });
    it("handles sprite completely outside buffer", () => {
        const buffer = createBuffer(10, 5);
        const sprite = ["ABC"];
        drawSprite(buffer, sprite, 100, 100, 10, 5);
        // Should not throw, buffer unchanged
        expect(bufferToString(buffer)).toBe("          \n          \n          \n          \n          ");
    });
    it("handles sparse lines array gracefully", () => {
        const buffer = createBuffer(10, 5);
        // Create sparse array with holes
        const sparseSprite = [];
        sparseSprite.length = 3;
        sparseSprite[0] = "AB";
        // sparseSprite[1] is undefined (hole)
        sparseSprite[2] = "CD";
        // Should not throw - the undefined check handles sparse arrays
        expect(() => {
            drawSprite(buffer, sparseSprite, 0, 0, 10, 5);
        }).not.toThrow();
        // First and third rows should be drawn
        expect(getCell(buffer, 0, 0)).toBe("A");
        expect(getCell(buffer, 0, 1)).toBe("B");
        expect(getCell(buffer, 2, 0)).toBe("C");
        expect(getCell(buffer, 2, 1)).toBe("D");
        // Second row (hole) should be skipped
        expect(getCell(buffer, 1, 0)).toBe(" ");
    });
    it("handles sparse buffer array gracefully", () => {
        // Create sparse buffer with holes
        const sparseBuffer = [];
        sparseBuffer.length = 5;
        sparseBuffer[0] = Array(10).fill(" ");
        sparseBuffer[4] = Array(10).fill(" ");
        // Middle rows are undefined (holes)
        const sprite = ["A", "B", "C", "D", "E"];
        // Should not throw - the undefined check handles sparse buffers
        expect(() => {
            drawSprite(sparseBuffer, sprite, 0, 0, 10, 5);
        }).not.toThrow();
        // Only rows 0 and 4 should be drawn (the non-sparse ones)
        // We explicitly set these rows above, so they are guaranteed to exist
        expect(getCell(sparseBuffer, 0, 0)).toBe("A");
        expect(getCell(sparseBuffer, 4, 0)).toBe("E");
    });
});
describe("drawSpriteFade", () => {
    beforeEach(() => {
        vi.spyOn(Math, "random");
    });
    afterEach(() => {
        vi.restoreAllMocks();
    });
    it("shows only old sprite at progress 0", () => {
        vi.mocked(Math.random).mockReturnValue(0.5);
        const buffer = createBuffer(10, 5);
        const oldSprite = ["A"];
        const newSprite = ["B"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 0, 0, 0, 10, 5, 0);
        // At progress 0, easedProgress = 0, so new sprite never shows (0.5 < 0 is false)
        // inverseEased = 1, so old sprite always shows (0.5 < 1 is true)
        expect(getCell(buffer, 0, 0)).toBe("A");
    });
    it("shows only new sprite at progress 1", () => {
        vi.mocked(Math.random).mockReturnValue(0.5);
        const buffer = createBuffer(10, 5);
        const oldSprite = ["A"];
        const newSprite = ["B"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 0, 0, 0, 10, 5, 1);
        // At progress 1, easedProgress = 1, so new sprite always shows (0.5 < 1 is true)
        expect(getCell(buffer, 0, 0)).toBe("B");
    });
    it("handles different positions for old and new sprites", () => {
        vi.mocked(Math.random).mockReturnValue(0.001); // Very low, only easedProgress > 0 will show new
        const buffer = createBuffer(10, 5);
        const oldSprite = ["A"];
        const newSprite = ["B"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 5, 0, 2, 10, 5, 1);
        // New sprite at (5, 2), old at (0, 0)
        expect(getCell(buffer, 2, 5)).toBe("B");
        expect(getCell(buffer, 0, 0)).toBe(" "); // Old not shown at progress 1
    });
    it("clips both sprites at boundaries", () => {
        vi.mocked(Math.random).mockReturnValue(0.5);
        const buffer = createBuffer(10, 5);
        const oldSprite = ["AAA"];
        const newSprite = ["BBB"];
        // Both partially outside
        drawSpriteFade(buffer, oldSprite, newSprite, -1, 8, 0, 0, 10, 5, 0.5);
        // Should not throw, some characters should be visible
        // Old clips at left, new clips at right
        const hasContent = buffer.some((row) => row.some((c) => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("handles empty sprites", () => {
        const buffer = createBuffer(10, 5);
        expect(() => {
            drawSpriteFade(buffer, [], [], 0, 0, 0, 0, 10, 5, 0.5);
        }).not.toThrow();
    });
    it("handles sparse lines arrays gracefully", () => {
        vi.mocked(Math.random).mockReturnValue(0.5);
        const buffer = createBuffer(10, 5);
        // Create sparse arrays with holes
        const sparseOld = [];
        sparseOld.length = 2;
        sparseOld[0] = "A";
        // sparseOld[1] is undefined
        const sparseNew = [];
        sparseNew.length = 2;
        // sparseNew[0] is undefined
        sparseNew[1] = "B";
        // Should not throw
        expect(() => {
            drawSpriteFade(buffer, sparseOld, sparseNew, 0, 0, 0, 0, 10, 5, 0.5);
        }).not.toThrow();
    });
    it("handles sparse buffer array gracefully", () => {
        vi.mocked(Math.random).mockReturnValue(0.5);
        // Create sparse buffer with holes
        const sparseBuffer = [];
        sparseBuffer.length = 5;
        sparseBuffer[0] = Array(10).fill(" ");
        sparseBuffer[4] = Array(10).fill(" ");
        // Middle rows are undefined (holes)
        const oldSprite = ["A", "B", "C"];
        const newSprite = ["X", "Y", "Z"];
        // Should not throw - the undefined check handles sparse buffers
        expect(() => {
            drawSpriteFade(sparseBuffer, oldSprite, newSprite, 0, 0, 0, 0, 10, 5, 0.5);
        }).not.toThrow();
    });
    it("handles rows outside height bounds", () => {
        vi.mocked(Math.random).mockReturnValue(0.5);
        const buffer = createBuffer(10, 5);
        const oldSprite = ["A"];
        const newSprite = ["B"];
        // Draw at y position that puts new sprite outside bounds
        expect(() => {
            drawSpriteFade(buffer, oldSprite, newSprite, 0, 0, 0, 10, 10, 5, 0.5);
        }).not.toThrow();
        // Draw at negative y position that puts old sprite outside bounds
        expect(() => {
            drawSpriteFade(buffer, oldSprite, newSprite, 0, 0, -5, 0, 10, 5, 0.5);
        }).not.toThrow();
    });
});
//# sourceMappingURL=draw.test.js.map