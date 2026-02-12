/**
 * Browser-specific I/O code.
 * This module contains code that requires browser APIs and is excluded from unit test coverage.
 * Testability is ensured through dependency injection in consuming modules.
 */

import type { AudioContextLike, AudioDependencies } from "../audio/types.js";

/**
 * Create browser AudioContext.
 *
 * Returns:
 *     AudioContext for Web Audio API.
 */
export function createBrowserAudioContext(): AudioContextLike {
  const AudioContextClass = window.AudioContext;
  return new AudioContextClass() as AudioContextLike;
}

/**
 * Create default audio dependencies for browser use.
 *
 * Returns:
 *     AudioDependencies with browser implementations.
 */
export function createDefaultAudioDependencies(): AudioDependencies {
  return {
    createContext: createBrowserAudioContext,
    fetchFn: (url: string) => fetch(url),
    addEventListenerFn: (type, handler): void => {
      document.addEventListener(type, handler);
    },
    removeEventListenerFn: (type, handler): void => {
      document.removeEventListener(type, handler);
    },
  };
}
