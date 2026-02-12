/**
 * Audio controller - manages audio playback lifecycle and track switching.
 * Initializes AudioContext on first user interaction to satisfy browser autoplay policies.
 */

import { createAudioPlayer, type AudioPlayer } from "./AudioPlayer.js";
import { getDefaultTrack } from "./TrackSelector.js";
import type { AudioTrack, AudioConfig, AudioDependencies, AudioContextLike } from "./types.js";

export type { AudioDependencies };

/** Debug log to screen overlay. */
function debug(msg: string): void {
  const win = window as unknown as { debugLog?: (m: string) => void };
  if (win.debugLog !== undefined) {
    win.debugLog(msg);
  } else {
    console.log(msg);
  }
}

/** Audio system state for track switching. */
export interface AudioSystem {
  context: AudioContextLike;
  player: AudioPlayer;
  tracks: readonly AudioTrack[];
  currentIndex: number;
  cleanup: () => void;
}

/**
 * Get track at index from tracks array.
 *
 * Args:
 *     tracks: Array of audio tracks.
 *     index: Index to retrieve.
 *
 * Returns:
 *     Track at index or undefined if out of bounds.
 */
function getTrackAtIndex(tracks: readonly AudioTrack[], index: number): AudioTrack | undefined {
  return tracks[index];
}

/** Type guard for KeyboardEvent. */
function isKeyboardEvent(e: Event): e is KeyboardEvent {
  return "key" in e;
}

/**
 * Switch to next track with crossfade.
 *
 * Args:
 *     audio: Audio system.
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
 *
 * Args:
 *     getAudio: Function returning audio system or null if not yet initialized.
 *     addListenerFn: Function to add event listener.
 */
export function setupTrackSwitcher(
  getAudio: () => AudioSystem | null,
  addListenerFn: (type: string, handler: (e: Event) => void) => void
): void {
  const handleKey = (e: Event): void => {
    if (isKeyboardEvent(e) && (e.key === "n" || e.key === "N")) {
      const audio = getAudio();
      if (audio !== null) {
        switchToNextTrack(audio);
      }
    }
  };
  addListenerFn("keydown", handleKey);
}

/** Deferred audio system created on first user interaction. */
export interface DeferredAudioSystem {
  tracks: readonly AudioTrack[];
  currentIndex: number;
  cleanup: () => void;
  getSystem: () => AudioSystem | null;
}

/**
 * Initialize audio system if enabled in config.
 * AudioContext is created lazily on first user interaction to satisfy
 * Android Chrome's requirement that AudioContext be created from a user gesture.
 *
 * Args:
 *     audioConfig: Audio configuration from config.json.
 *     deps: Audio dependencies.
 *
 * Returns:
 *     Deferred audio system or null if disabled.
 */
export function initializeAudio(
  audioConfig: AudioConfig | undefined,
  deps: AudioDependencies
): DeferredAudioSystem | null {
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

  let system: AudioSystem | null = null;

  const start = (): void => {
    debug("[Audio] start() called");
    if (system !== null) {
      debug("[Audio] system already exists, returning");
      return;
    }

    debug("[Audio] Creating AudioContext...");
    const context = deps.createContext();
    debug(`[Audio] AudioContext created, state: ${context.state}`);

    const player = createAudioPlayer({
      context,
      fetchFn: deps.fetchFn,
      masterVolume: audioConfig.masterVolume,
    });
    debug("[Audio] Player created");

    system = {
      context,
      player,
      tracks: audioConfig.tracks,
      currentIndex: 0,
      cleanup: (): void => {
        deps.removeEventListenerFn("click", start);
        deps.removeEventListenerFn("touchstart", start);
        deps.removeEventListenerFn("touchend", start);
        deps.removeEventListenerFn("keydown", start);
      },
    };

    if (context.state === "suspended") {
      debug("[Audio] Context suspended, calling resume()...");
      // Android Chrome: resume() promise may hang, so use timeout fallback
      let played = false;
      const playOnce = (): void => {
        if (!played) {
          played = true;
          debug(`[Audio] Playing track: ${track.id}`);
          player.play(track);
        }
      };
      // Try resume and play when it resolves
      context.resume().then(() => {
        debug("[Audio] Resume succeeded");
        playOnce();
      }).catch((err) => {
        debug(`[Audio] Resume failed: ${String(err)}`);
        playOnce();
      });
      // Fallback: play after 500ms if resume hangs
      setTimeout(() => {
        debug("[Audio] Timeout fallback triggered");
        playOnce();
      }, 500);
    } else {
      debug(`[Audio] Context running, playing track: ${track.id}`);
      player.play(track);
    }

    deps.removeEventListenerFn("click", start);
    deps.removeEventListenerFn("touchstart", start);
    deps.removeEventListenerFn("touchend", start);
    deps.removeEventListenerFn("keydown", start);
  };

  deps.addEventListenerFn("click", start);
  deps.addEventListenerFn("touchstart", start);
  deps.addEventListenerFn("touchend", start);
  deps.addEventListenerFn("keydown", start);

  return {
    tracks: audioConfig.tracks,
    currentIndex: 0,
    cleanup: (): void => {
      deps.removeEventListenerFn("click", start);
      deps.removeEventListenerFn("touchstart", start);
      deps.removeEventListenerFn("touchend", start);
      deps.removeEventListenerFn("keydown", start);
    },
    getSystem: (): AudioSystem | null => system,
  };
}

/** Test hooks for internal functions. */
export const _test_hooks = {
  getTrackAtIndex,
  isKeyboardEvent,
  switchToNextTrack,
  setupTrackSwitcher,
  initializeAudio,
};
