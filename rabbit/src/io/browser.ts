/**
 * Browser-specific I/O code.
 * This module contains code that requires browser APIs and is excluded from unit test coverage.
 * Testability is ensured through dependency injection in consuming modules.
 */

import type { AudioContextLike, AudioDependencies } from "../audio/types.js";

/** Window with webkit audio context for older browsers. */
interface WindowWithWebkit extends Window {
  AudioContext?: typeof AudioContext;
  webkitAudioContext?: typeof AudioContext;
}

/**
 * Create browser AudioContext.
 * Uses the same pattern as kana-pop AudioService for maximum compatibility.
 *
 * Returns:
 *     AudioContext for Web Audio API.
 */
export function createBrowserAudioContext(): AudioContextLike {
  const win = window as WindowWithWebkit;
  // Set global AudioContext like kana-pop does
  const AudioContextClass = win.AudioContext ?? win.webkitAudioContext;
  if (AudioContextClass === undefined) {
    throw new Error("Web Audio API not supported");
  }
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
