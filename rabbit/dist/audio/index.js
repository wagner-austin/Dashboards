/**
 * Audio module public API.
 * Re-exports types, validation, track selection, and player.
 */
export { createAudioState } from "./types.js";
// Validation
export { validateAudioConfig } from "./validation.js";
// Track selection
export { selectTrackByTime, selectTrackByLocation, getDefaultTrack, } from "./TrackSelector.js";
export { createAudioPlayer } from "./AudioPlayer.js";
export { setupAudioStart, switchToNextTrack, setupTrackSwitcher, initializeAudio, } from "./controller.js";
// Browser-specific (from io module)
export { createBrowserAudioContext, createDefaultAudioDependencies } from "../io/browser.js";
//# sourceMappingURL=index.js.map