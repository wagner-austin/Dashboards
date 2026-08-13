/**
 * Viewport measurement and buffer management.
 */
export function measureViewport(screen) {
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
export function createBuffer(width, height) {
    return Array.from({ length: height }, () => Array(width).fill(" "));
}
export function renderBuffer(buffer) {
    return buffer.map((row) => row.join("")).join("\n");
}
/** Test hooks for internal functions */
export const _test_hooks = {
    measureViewport,
    createBuffer,
    renderBuffer,
};
//# sourceMappingURL=Viewport.js.map