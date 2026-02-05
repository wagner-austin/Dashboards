/**
 * @vitest-environment jsdom
 * Tests for Viewport measurement and buffer management.
 */
import { describe, it, expect, vi } from "vitest";
import { createBuffer, renderBuffer, measureViewport } from "./Viewport.js";
describe("createBuffer", () => {
    it("creates buffer with correct dimensions", () => {
        const buffer = createBuffer(10, 5);
        expect(buffer.length).toBe(5);
        for (const row of buffer) {
            expect(row.length).toBe(10);
        }
    });
    it("fills buffer with spaces", () => {
        const buffer = createBuffer(3, 2);
        for (const row of buffer) {
            for (const cell of row) {
                expect(cell).toBe(" ");
            }
        }
    });
    it("handles zero dimensions", () => {
        const buffer = createBuffer(0, 0);
        expect(buffer.length).toBe(0);
    });
    it("creates independent rows", () => {
        const buffer = createBuffer(5, 3);
        const row0 = buffer[0];
        const row1 = buffer[1];
        const row2 = buffer[2];
        if (row0 === undefined || row1 === undefined || row2 === undefined) {
            throw new Error("Expected buffer to have 3 rows");
        }
        row0[0] = "X";
        expect(row1[0]).toBe(" ");
        expect(row2[0]).toBe(" ");
    });
});
describe("renderBuffer", () => {
    it("joins rows with newlines", () => {
        const buffer = [
            ["A", "B", "C"],
            ["D", "E", "F"],
        ];
        expect(renderBuffer(buffer)).toBe("ABC\nDEF");
    });
    it("handles empty buffer", () => {
        expect(renderBuffer([])).toBe("");
    });
    it("handles single row", () => {
        const buffer = [["X", "Y", "Z"]];
        expect(renderBuffer(buffer)).toBe("XYZ");
    });
});
describe("measureViewport", () => {
    it("calculates dimensions from client size and character size", () => {
        // Mock document.documentElement
        const originalDocumentElement = document.documentElement;
        Object.defineProperty(document, "documentElement", {
            value: {
                clientWidth: 800,
                clientHeight: 600,
            },
            writable: true,
            configurable: true,
        });
        // Mock HTMLPreElement
        const mockScreen = {
            textContent: "",
            getBoundingClientRect: vi.fn().mockReturnValue({
                width: 10,
                height: 20,
            }),
        };
        const viewport = measureViewport(mockScreen);
        expect(viewport.width).toBe(80); // 800 / 10
        expect(viewport.height).toBe(30); // 600 / 20
        expect(viewport.charW).toBe(10);
        expect(viewport.charH).toBe(20);
        expect(mockScreen.textContent).toBe("");
        // Restore
        Object.defineProperty(document, "documentElement", {
            value: originalDocumentElement,
            writable: true,
            configurable: true,
        });
    });
});
//# sourceMappingURL=Viewport.test.js.map