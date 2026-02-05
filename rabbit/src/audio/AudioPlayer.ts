/**
 * Audio player with dependency injection for testability.
 * Uses HTMLAudioElement for cross-browser compatibility.
 * Supports fade-in on start and crossfade between tracks.
 */

import type { AudioTrack, AudioState, AudioElementLike } from "./types.js";

export type { AudioElementLike };

/** Audio player interface */
export interface AudioPlayer {
  play(track: AudioTrack): void;
  pause(): void;
  resume(): void;
  setVolume(volume: number): void;
  getState(): AudioState;
}

/** Dependencies for audio player */
export interface AudioPlayerDeps {
  createElement: () => AudioElementLike;
  masterVolume: number;
}

/** Fade operation tracking */
interface FadeOperation {
  interval: ReturnType<typeof setInterval>;
  element: AudioElementLike;
}

/** Internal mutable state for audio player */
interface AudioPlayerInternalState {
  currentTrackId: string | null;
  currentTrack: AudioTrack | null;
  isPlaying: boolean;
  volume: number;
  element: AudioElementLike | null;
  fadeIn: FadeOperation | null;
  fadeOuts: FadeOperation[];
}

/** Default fade duration in milliseconds */
const FADE_DURATION_MS = 1000;
const FADE_STEPS = 20;

/**
 * Create audio player with injected dependencies.
 * Allows testing without actual Audio elements.
 */
export function createAudioPlayer(deps: AudioPlayerDeps): AudioPlayer {
  const state: AudioPlayerInternalState = {
    currentTrackId: null,
    currentTrack: null,
    isPlaying: false,
    volume: deps.masterVolume,
    element: null,
    fadeIn: null,
    fadeOuts: [],
  };

  function calculateVolume(trackVolume: number): number {
    return state.volume * trackVolume;
  }

  function stopFadeIn(): void {
    if (state.fadeIn !== null) {
      clearInterval(state.fadeIn.interval);
      state.fadeIn = null;
    }
  }

  function removeFadeOutByInterval(interval: ReturnType<typeof setInterval>): void {
    clearInterval(interval);
    state.fadeOuts = state.fadeOuts.filter(f => f.interval !== interval);
  }

  function stopAllFadeOuts(): void {
    for (const fadeOp of state.fadeOuts) {
      clearInterval(fadeOp.interval);
    }
    state.fadeOuts = [];
  }

  function fadeIn(element: AudioElementLike, targetVolume: number): void {
    stopFadeIn();
    const stepDuration = FADE_DURATION_MS / FADE_STEPS;
    const volumeStep = targetVolume / FADE_STEPS;
    let currentStep = 0;

    element.volume = 0;

    const interval = setInterval(() => {
      currentStep++;
      const newVolume = Math.min(volumeStep * currentStep, targetVolume);
      element.volume = newVolume;

      if (currentStep >= FADE_STEPS) {
        stopFadeIn();
      }
    }, stepDuration);

    state.fadeIn = { interval, element };
  }

  function fadeOut(element: AudioElementLike, startVolume: number): void {
    const stepDuration = FADE_DURATION_MS / FADE_STEPS;
    const volumeStep = startVolume / FADE_STEPS;
    let currentStep = 0;

    const interval = setInterval(() => {
      currentStep++;
      const newVolume = Math.max(startVolume - volumeStep * currentStep, 0);
      element.volume = newVolume;

      if (currentStep >= FADE_STEPS) {
        element.pause();
        removeFadeOutByInterval(interval);
      }
    }, stepDuration);

    state.fadeOuts.push({ interval, element });
  }

  function play(track: AudioTrack): void {
    // If there's a current element playing, crossfade out
    if (state.element !== null) {
      const oldElement = state.element;
      const oldVolume = oldElement.volume;
      stopFadeIn(); // Stop any in-progress fade-in on old element
      fadeOut(oldElement, oldVolume);
    }

    // Create new element
    const element = deps.createElement();
    state.element = element;
    state.currentTrackId = track.id;
    state.currentTrack = track;

    // Configure element
    element.src = track.path;
    element.loop = track.loop;
    const targetVolume = calculateVolume(track.volume);
    element.volume = 0; // Start silent for fade-in

    // Start playback with fade-in
    state.isPlaying = true;
    element.play().then(() => {
      fadeIn(element, targetVolume);
    }).catch(() => {
      // Autoplay may be blocked - state remains "playing" awaiting user interaction
    });
  }

  function pause(): void {
    stopFadeIn();
    stopAllFadeOuts();
    if (state.element !== null) {
      state.element.pause();
    }
    state.isPlaying = false;
  }

  function resume(): void {
    if (state.element !== null && !state.isPlaying) {
      state.isPlaying = true;
      state.element.play().catch(() => {
        // May fail if not resumed from user interaction
      });
    }
  }

  function setVolume(volume: number): void {
    // Clamp volume to valid range
    const clampedVolume = Math.max(0, Math.min(1, volume));
    state.volume = clampedVolume;

    // Update element volume if playing
    if (state.element !== null && state.currentTrack !== null) {
      state.element.volume = calculateVolume(state.currentTrack.volume);
    }
  }

  function getState(): AudioState {
    return {
      currentTrackId: state.currentTrackId,
      isPlaying: state.isPlaying,
      volume: state.volume,
    };
  }

  return {
    play,
    pause,
    resume,
    setVolume,
    getState,
  };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  createAudioPlayer,
};
