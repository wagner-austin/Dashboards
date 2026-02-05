/**
 * Browser-specific I/O code.
 * This module contains code that requires browser APIs and is excluded from unit test coverage.
 * Testability is ensured through dependency injection in consuming modules.
 */
/**
 * Create browser audio element.
 * Returns a real HTMLAudioElement for browser use.
 */
export function createBrowserAudioElement() {
    return new Audio();
}
/**
 * Create default audio dependencies for browser use.
 */
export function createDefaultAudioDependencies() {
    return {
        createElementFn: createBrowserAudioElement,
        addEventListenerFn: (type, handler) => {
            document.addEventListener(type, handler);
        },
        removeEventListenerFn: (type, handler) => {
            document.removeEventListener(type, handler);
        },
    };
}
//# sourceMappingURL=browser.js.map