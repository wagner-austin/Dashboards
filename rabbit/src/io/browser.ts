/**
 * Browser-specific I/O code.
 * This module contains code that requires browser APIs and is excluded from unit test coverage.
 * Testability is ensured through dependency injection in consuming modules.
 */

import type { AudioElementLike, AudioDependencies } from "../audio/types.js";

/**
 * Create browser audio element.
 * Returns a real HTMLAudioElement for browser use.
 */
export function createBrowserAudioElement(): AudioElementLike {
  return new Audio();
}

/**
 * Create default audio dependencies for browser use.
 */
export function createDefaultAudioDependencies(): AudioDependencies {
  return {
    createElementFn: createBrowserAudioElement,
    addEventListenerFn: (type, handler): void => {
      document.addEventListener(type, handler);
    },
    removeEventListenerFn: (type, handler): void => {
      document.removeEventListener(type, handler);
    },
  };
}
