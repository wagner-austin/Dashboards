/**
 * Viewport measurement and buffer management.
 */
export interface ViewportState {
    width: number;
    height: number;
    charW: number;
    charH: number;
}
export declare function measureViewport(screen: HTMLPreElement): ViewportState;
export declare function createBuffer(width: number, height: number): string[][];
export declare function renderBuffer(buffer: string[][]): string;
//# sourceMappingURL=Viewport.d.ts.map