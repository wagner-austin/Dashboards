/**
 * Browser-specific I/O code.
 * This module contains code that requires browser APIs and is excluded from unit test coverage.
 * Testability is ensured through dependency injection in consuming modules.
 */
/**
 * Create browser AudioContext.
 * Uses the same pattern as kana-pop AudioService for maximum compatibility.
 *
 * Returns:
 *     AudioContext for Web Audio API.
 */
export function createBrowserAudioContext() {
    const win = window;
    // Set global AudioContext like kana-pop does
    const AudioContextClass = win.AudioContext ?? win.webkitAudioContext;
    if (AudioContextClass === undefined) {
        throw new Error("Web Audio API not supported");
    }
    return new AudioContextClass();
}
/**
 * Create default audio dependencies for browser use.
 *
 * Returns:
 *     AudioDependencies with browser implementations.
 */
export function createDefaultAudioDependencies() {
    return {
        createContext: createBrowserAudioContext,
        fetchFn: (url) => fetch(url),
        addEventListenerFn: (type, handler) => {
            document.addEventListener(type, handler);
        },
        removeEventListenerFn: (type, handler) => {
            document.removeEventListener(type, handler);
        },
    };
}
//# sourceMappingURL=browser.js.map