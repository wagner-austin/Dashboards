/**
 * Tests for sprite drawing functions.
 */
import { describe, it, expect } from "vitest";
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
        expect(bufferToString(buffer)).toBe("          \n          \n          \n          \n          ");
    });
    it("handles sprite completely outside buffer", () => {
        const buffer = createBuffer(10, 5);
        const sprite = ["ABC"];
        drawSprite(buffer, sprite, 100, 100, 10, 5);
        expect(bufferToString(buffer)).toBe("          \n          \n          \n          \n          ");
    });
    it("handles sparse lines array gracefully", () => {
        const buffer = createBuffer(10, 5);
        const sparseSprite = [];
        sparseSprite.length = 3;
        sparseSprite[0] = "AB";
        sparseSprite[2] = "CD";
        expect(() => {
            drawSprite(buffer, sparseSprite, 0, 0, 10, 5);
        }).not.toThrow();
        expect(getCell(buffer, 0, 0)).toBe("A");
        expect(getCell(buffer, 0, 1)).toBe("B");
        expect(getCell(buffer, 2, 0)).toBe("C");
        expect(getCell(buffer, 2, 1)).toBe("D");
        expect(getCell(buffer, 1, 0)).toBe(" ");
    });
    it("handles sparse buffer array gracefully", () => {
        const sparseBuffer = [];
        sparseBuffer.length = 5;
        sparseBuffer[0] = Array(10).fill(" ");
        sparseBuffer[4] = Array(10).fill(" ");
        const sprite = ["A", "B", "C", "D", "E"];
        expect(() => {
            drawSprite(sparseBuffer, sprite, 0, 0, 10, 5);
        }).not.toThrow();
        expect(getCell(sparseBuffer, 0, 0)).toBe("A");
        expect(getCell(sparseBuffer, 4, 0)).toBe("E");
    });
});
describe("drawSpriteFade", () => {
    it("shows only old sprite at progress 0", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = ["A"];
        const newSprite = ["B"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 0);
        expect(getCell(buffer, 0, 0)).toBe("A");
    });
    it("shows only new sprite at progress 1", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = ["A"];
        const newSprite = ["B"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 1);
        expect(getCell(buffer, 0, 0)).toBe("B");
    });
    it("draws sprites at different Y positions", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = ["A"];
        const newSprite = ["B"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 3, 1, 1, 10, 5, 1);
        expect(getCell(buffer, 2, 0)).toBe("B");
    });
    it("clips sprites at boundaries", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = ["AAA"];
        const newSprite = ["BBB"];
        drawSpriteFade(buffer, oldSprite, newSprite, 1, 1, 1, 1, 3, 3, 10, 5, 0.5);
        const hasContent = buffer.some((row) => row.some((c) => c !== " "));
        expect(hasContent).toBe(true);
    });
    it("handles empty sprites", () => {
        const buffer = createBuffer(10, 5);
        expect(() => {
            drawSpriteFade(buffer, [], [], 5, 3, 5, 3, 0, 0, 10, 5, 0.5);
        }).not.toThrow();
    });
    it("handles sparse lines arrays gracefully", () => {
        const buffer = createBuffer(10, 5);
        const sparseOld = [];
        sparseOld.length = 2;
        sparseOld[0] = "A";
        const sparseNew = [];
        sparseNew.length = 2;
        sparseNew[1] = "B";
        expect(() => {
            drawSpriteFade(buffer, sparseOld, sparseNew, 5, 3, 5, 3, 1, 1, 10, 5, 0.5);
        }).not.toThrow();
    });
    it("handles sparse buffer array gracefully", () => {
        const sparseBuffer = [];
        sparseBuffer.length = 5;
        sparseBuffer[0] = Array(10).fill(" ");
        sparseBuffer[4] = Array(10).fill(" ");
        const oldSprite = ["A", "B", "C"];
        const newSprite = ["X", "Y", "Z"];
        expect(() => {
            drawSpriteFade(sparseBuffer, oldSprite, newSprite, 5, 4, 5, 4, 1, 1, 10, 5, 0.5);
        }).not.toThrow();
    });
    it("handles sprites outside bounds", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = ["A"];
        const newSprite = ["B"];
        expect(() => {
            drawSpriteFade(buffer, oldSprite, newSprite, 5, 10, 5, 10, 1, 1, 10, 5, 0.5);
        }).not.toThrow();
        expect(() => {
            drawSpriteFade(buffer, oldSprite, newSprite, 5, -5, 5, -5, 1, 1, 10, 5, 0.5);
        }).not.toThrow();
    });
    it("returns early when visibility is zero", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = ["A"];
        const newSprite = ["B"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 0);
        expect(getCell(buffer, 0, 0)).toBe(" ");
    });
    it("fades character through gradient at partial visibility", () => {
        const buffer = createBuffer(10, 5);
        // Use # which is density 0, at visibility 0.5 it fades to density 2 (=)
        const oldSprite = ["#"];
        const newSprite = ["#"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 0.5);
        // At visibility 0.5: fadeAmount = floor((1-0.5) * 5) = 2, result = "="
        expect(getCell(buffer, 0, 0)).toBe("=");
    });
    it("draws same character without transition when both sprites match", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = ["X"];
        const newSprite = ["X"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 1);
        expect(getCell(buffer, 0, 0)).toBe("X");
    });
    it("fades same characters through gradient at low visibility", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = ["#"];
        const newSprite = ["#"];
        // Very low visibility - should fade to nearly empty
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 0.1);
        // At visibility 0.1: fadeAmount = floor((1-0.1) * 5) = 4, result = ":"
        expect(getCell(buffer, 0, 0)).toBe(":");
    });
    it("handles zero-size sprites for maxDist edge case", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = [""];
        const newSprite = [""];
        expect(() => {
            drawSpriteFade(buffer, oldSprite, newSprite, 5, 3, 5, 3, 0, 0, 10, 5, 0.5);
        }).not.toThrow();
    });
    it("handles transition with space characters", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = [" "];
        const newSprite = [" "];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 1);
        expect(getCell(buffer, 0, 0)).toBe(" ");
    });
    it("fades different characters through gradient", () => {
        const buffer = createBuffer(10, 5);
        // Use gradient characters to verify fading
        const oldSprite = ["#"];
        const newSprite = ["+"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 0.5);
        // Result depends on which char is selected by transition, then faded
        const result = getCell(buffer, 0, 0);
        // Should be a faded gradient character: # → = or + → -
        expect(["=", "-", "#", "+"]).toContain(result);
    });
    it("draws when visibility is exactly 1", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = ["A"];
        const newSprite = ["B"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 1, 1);
        expect(getCell(buffer, 0, 0)).toBe("B");
    });
    it("preserves gradient characters at full visibility", () => {
        const buffer = createBuffer(10, 5);
        const oldSprite = ["+"];
        const newSprite = ["+"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 1);
        // At full visibility, character is unchanged
        expect(getCell(buffer, 0, 0)).toBe("+");
    });
    it("fades gradient character to lighter version", () => {
        const buffer = createBuffer(10, 5);
        // "+" is density 1, at visibility 0.5: fadeAmount = floor(0.5 * 4) = 2
        // resultLevel = 1 + 2 = 3 = "-"
        const oldSprite = ["+"];
        const newSprite = ["+"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 0.5);
        expect(getCell(buffer, 0, 0)).toBe("-");
    });
    it("covers all gradient density levels when fading", () => {
        // Test levels 0-5 through the formula (visibility > 0 and < 1)
        // Gradient: # → + → = → - → : → . → (space)
        // From "#" (level 0), fadeAmount = floor((1 - visibility) * 5)
        const testCases = [
            { char: "#", visibility: 0.99, expected: "#" }, // Level 0: fadeAmount = 0
            { char: "#", visibility: 0.75, expected: "+" }, // Level 1: fadeAmount = floor(1.25) = 1
            { char: "#", visibility: 0.55, expected: "=" }, // Level 2: fadeAmount = floor(2.25) = 2
            { char: "#", visibility: 0.35, expected: "-" }, // Level 3: fadeAmount = floor(3.25) = 3
            { char: "#", visibility: 0.15, expected: ":" }, // Level 4: fadeAmount = floor(4.25) = 4
            { char: ".", visibility: 0.5, expected: "." }, // Level 5: fadeSteps = 0, stays at "."
        ];
        for (const { char, visibility, expected } of testCases) {
            const buffer = createBuffer(10, 5);
            drawSpriteFade(buffer, [char], [char], 0, 1, 0, 1, 1, 1, 10, 5, 0.5, visibility);
            expect(getCell(buffer, 0, 0)).toBe(expected);
        }
        // Space via early return at visibility <= 0
        const buffer = createBuffer(10, 5);
        drawSpriteFade(buffer, ["#"], ["#"], 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 0);
        expect(getCell(buffer, 0, 0)).toBe(" ");
    });
    it("fades from + character through gradient", () => {
        const buffer = createBuffer(10, 5);
        // "+" is density 1, at visibility 0.5: fadeAmount = floor(0.5 * 4) = 2
        // resultLevel = 1 + 2 = 3 = "-"
        drawSpriteFade(buffer, ["+"], ["+"], 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 0.5);
        expect(getCell(buffer, 0, 0)).toBe("-");
    });
    it("fades from - character through gradient", () => {
        const buffer = createBuffer(10, 5);
        // "-" is density 3, at visibility 0.5: fadeAmount = floor(0.5 * 2) = 1
        // resultLevel = 3 + 1 = 4 = ":"
        drawSpriteFade(buffer, ["-"], ["-"], 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 0.5);
        expect(getCell(buffer, 0, 0)).toBe(":");
    });
    it("fades from . character through gradient", () => {
        const buffer = createBuffer(10, 5);
        // "." is density 5, at visibility 0.5: fadeAmount = floor(0.5 * 0) = 0
        // resultLevel = 5 + 0 = 5 = "."
        drawSpriteFade(buffer, ["."], ["."], 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 0.5);
        expect(getCell(buffer, 0, 0)).toBe(".");
    });
    it("treats unknown characters as maximum density when fading", () => {
        const buffer = createBuffer(10, 5);
        // "X" is not in CHAR_DENSITY, should use default 0 (maximum density)
        // At visibility 0.5: fadeAmount = floor(0.5 * 5) = 2, result = "="
        drawSpriteFade(buffer, ["X"], ["X"], 0, 1, 0, 1, 1, 1, 10, 5, 0.5, 0.5);
        expect(getCell(buffer, 0, 0)).toBe("=");
    });
    it("clips columns extending beyond left edge", () => {
        const buffer = createBuffer(10, 5);
        // Wide sprite with center at x=0, width=6 means drawing from x=-3 to x=2
        // Columns at -3, -2, -1 should be clipped
        const oldSprite = ["ABCDEF"];
        const newSprite = ["ABCDEF"];
        drawSpriteFade(buffer, oldSprite, newSprite, 0, 1, 0, 1, 6, 6, 10, 5, 0.5, 1);
        // Only columns 0-2 should have content (D, E, F from right half)
        const hasContent = buffer.some((row) => row.some((c) => c !== " "));
        expect(hasContent).toBe(true);
        // Left edge of buffer should have content from sprite
        expect(getCell(buffer, 0, 0)).not.toBe(" ");
    });
    it("clips columns extending beyond right edge", () => {
        const buffer = createBuffer(10, 5);
        // Wide sprite with center at x=9, width=6 means drawing from x=6 to x=11
        // Columns at 10, 11 should be clipped
        const oldSprite = ["ABCDEF"];
        const newSprite = ["ABCDEF"];
        drawSpriteFade(buffer, oldSprite, newSprite, 9, 1, 9, 1, 6, 6, 10, 5, 0.5, 1);
        // Only columns 6-9 should have content
        const hasContent = buffer.some((row) => row.some((c) => c !== " "));
        expect(hasContent).toBe(true);
        // Right edge should have content
        expect(getCell(buffer, 0, 9)).not.toBe(" ");
    });
});
//# sourceMappingURL=draw.test.js.map