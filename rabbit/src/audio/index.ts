/**
 * Audio module public API.
 * Re-exports types, validation, track selection, and player.
 */

// Types
export type {
  TimeOfDay,
  TrackTags,
  AudioTrack,
  AudioConfig,
  AudioState,
  AudioElementLike,
  AudioDependencies,
} from "./types.js";
export { createAudioState } from "./types.js";

// Validation
export { validateAudioConfig } from "./validation.js";

// Track selection
export {
  selectTrackByTime,
  selectTrackByLocation,
  getDefaultTrack,
} from "./TrackSelector.js";

// Audio player
export type {
  AudioPlayer,
  AudioPlayerDeps,
} from "./AudioPlayer.js";
export { createAudioPlayer } from "./AudioPlayer.js";

// Audio controller
export type { AudioSystem } from "./controller.js";
export {
  setupAudioStart,
  switchToNextTrack,
  setupTrackSwitcher,
  initializeAudio,
} from "./controller.js";

// Browser-specific (from io module)
export { createBrowserAudioElement, createDefaultAudioDependencies } from "../io/browser.js";
