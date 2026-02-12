/**
 * Audio module public API.
 * Re-exports types, validation, track selection, and player.
 */
export type { TimeOfDay, TrackTags, AudioTrack, AudioConfig, AudioState, AudioContextLike, AudioBufferSourceNodeLike, GainNodeLike, AudioParamLike, AudioDependencies, } from "./types.js";
export { createAudioState } from "./types.js";
export { validateAudioConfig } from "./validation.js";
export { selectTrackByTime, selectTrackByLocation, getDefaultTrack, } from "./TrackSelector.js";
export type { AudioPlayer, AudioPlayerDeps, } from "./AudioPlayer.js";
export { createAudioPlayer } from "./AudioPlayer.js";
export type { AudioSystem } from "./controller.js";
export { setupAudioStart, switchToNextTrack, setupTrackSwitcher, initializeAudio, } from "./controller.js";
export { createBrowserAudioContext, createDefaultAudioDependencies } from "../io/browser.js";
//# sourceMappingURL=index.d.ts.map