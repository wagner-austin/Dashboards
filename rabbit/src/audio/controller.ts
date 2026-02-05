/**
 * Audio controller - manages audio playback lifecycle and track switching.
 * Handles browser autoplay restrictions via user interaction triggers.
 */

import { createAudioPlayer, type AudioPlayer } from "./AudioPlayer.js";
import { getDefaultTrack } from "./TrackSelector.js";
import type { AudioTrack, AudioConfig, AudioDependencies } from "./types.js";

export type { AudioDependencies };

/** Audio system state for track switching */
export interface AudioSystem {
  player: AudioPlayer;
  tracks: readonly AudioTrack[];
  currentIndex: number;
  cleanup: () => void;
}

/**
 * Get track at index from tracks array.
 * Returns undefined if index is out of bounds.
 */
function getTrackAtIndex(tracks: readonly AudioTrack[], index: number): AudioTrack | undefined {
  return tracks[index];
}

/** Type guard for KeyboardEvent */
function isKeyboardEvent(e: Event): e is KeyboardEvent {
  return "key" in e;
}

/**
 * Setup audio to start on first user interaction.
 * Required for iOS/Safari which blocks autoplay.
 */
export function setupAudioStart(
  player: AudioPlayer,
  track: AudioTrack,
  deps: AudioDependencies
): () => void {
  const start = (): void => {
    player.play(track);
    deps.removeEventListenerFn("click", start);
    deps.removeEventListenerFn("touchstart", start);
    deps.removeEventListenerFn("keydown", start);
  };
  deps.addEventListenerFn("click", start);
  deps.addEventListenerFn("touchstart", start);
  deps.addEventListenerFn("keydown", start);
  return start;
}

/**
 * Switch to next track with crossfade.
 * Cycles through available tracks.
 */
export function switchToNextTrack(audio: AudioSystem): void {
  const trackCount = audio.tracks.length;
  if (trackCount <= 1) {
    return;
  }
  const nextIndex = (audio.currentIndex + 1) % trackCount;
  const nextTrack = getTrackAtIndex(audio.tracks, nextIndex);
  if (nextTrack === undefined) {
    return;
  }
  audio.currentIndex = nextIndex;
  audio.player.play(nextTrack);
}

/**
 * Setup keyboard listener for track switching (N key).
 */
export function setupTrackSwitcher(
  audio: AudioSystem,
  addListenerFn: (type: string, handler: (e: Event) => void) => void
): void {
  const handleKey = (e: Event): void => {
    if (isKeyboardEvent(e) && (e.key === "n" || e.key === "N")) {
      switchToNextTrack(audio);
    }
  };
  addListenerFn("keydown", handleKey);
}

/**
 * Initialize audio player if audio is enabled in config.
 * Returns the audio system with player and tracks, or null if disabled.
 */
export function initializeAudio(
  audioConfig: AudioConfig | undefined,
  deps: AudioDependencies
): AudioSystem | null {
  if (audioConfig === undefined) {
    return null;
  }
  if (!audioConfig.enabled) {
    return null;
  }

  const track = getDefaultTrack(audioConfig.tracks);
  if (track === null) {
    return null;
  }

  const player = createAudioPlayer({
    createElement: deps.createElementFn,
    masterVolume: audioConfig.masterVolume,
  });

  const cleanup = setupAudioStart(player, track, deps);

  return {
    player,
    tracks: audioConfig.tracks,
    currentIndex: 0,
    cleanup,
  };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  getTrackAtIndex,
  isKeyboardEvent,
  setupAudioStart,
  switchToNextTrack,
  setupTrackSwitcher,
  initializeAudio,
};
