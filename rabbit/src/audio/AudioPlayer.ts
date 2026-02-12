/**
 * Audio player using Web Audio API.
 * Fetches audio as ArrayBuffer, decodes to AudioBuffer, plays via BufferSourceNode.
 * Supports crossfade between tracks using GainNode ramping.
 */

import type {
  AudioTrack,
  AudioState,
  AudioContextLike,
  AudioBufferSourceNodeLike,
  GainNodeLike,
  FetchFn,
} from "./types.js";

/** Audio player interface. */
export interface AudioPlayer {
  play(track: AudioTrack): void;
  pause(): void;
  resume(): void;
  setVolume(volume: number): void;
  getState(): AudioState;
}

/** Dependencies for audio player. */
export interface AudioPlayerDeps {
  context: AudioContextLike;
  fetchFn: FetchFn;
  masterVolume: number;
}

/** Active source with gain control. */
interface ActiveSource {
  source: AudioBufferSourceNodeLike;
  gain: GainNodeLike;
  track: AudioTrack;
}

/** Fade duration in seconds. */
const FADE_DURATION = 1.0;

/** Internal mutable state. */
interface AudioPlayerState {
  currentTrackId: string | null;
  isPlaying: boolean;
  volume: number;
  buffers: Map<string, AudioBuffer>;
  activeSource: ActiveSource | null;
  fadingOutSources: ActiveSource[];
}

/**
 * Create audio player with Web Audio API.
 *
 * Args:
 *     deps: Audio player dependencies.
 *
 * Returns:
 *     AudioPlayer instance.
 */
export function createAudioPlayer(deps: AudioPlayerDeps): AudioPlayer {
  const state: AudioPlayerState = {
    currentTrackId: null,
    isPlaying: false,
    volume: deps.masterVolume,
    buffers: new Map(),
    activeSource: null,
    fadingOutSources: [],
  };

  function calculateVolume(trackVolume: number): number {
    return state.volume * trackVolume;
  }

  async function loadBuffer(track: AudioTrack): Promise<AudioBuffer | null> {
    const cached = state.buffers.get(track.id);
    if (cached !== undefined) {
      return cached;
    }

    const response = await deps.fetchFn(track.path);
    if (!response.ok) {
      return null;
    }

    const arrayBuffer = await response.arrayBuffer();
    const audioBuffer = await deps.context.decodeAudioData(arrayBuffer);
    state.buffers.set(track.id, audioBuffer);
    return audioBuffer;
  }

  function fadeOut(active: ActiveSource): void {
    const currentTime = 0;
    active.gain.gain.linearRampToValueAtTime(0, currentTime + FADE_DURATION);
    state.fadingOutSources.push(active);

    setTimeout(() => {
      active.source.stop();
      state.fadingOutSources = state.fadingOutSources.filter(s => s !== active);
    }, FADE_DURATION * 1000);
  }

  function createSource(buffer: AudioBuffer, track: AudioTrack): ActiveSource {
    const source = deps.context.createBufferSource();
    source.buffer = buffer;
    source.loop = track.loop;

    const gain = deps.context.createGain();
    gain.gain.value = 0;

    source.connect(gain);
    gain.connect(deps.context.destination);

    return { source, gain, track };
  }

  function fadeIn(active: ActiveSource): void {
    const targetVolume = calculateVolume(active.track.volume);
    const currentTime = 0;
    active.gain.gain.linearRampToValueAtTime(targetVolume, currentTime + FADE_DURATION);
  }

  function play(track: AudioTrack): void {
    state.currentTrackId = track.id;
    state.isPlaying = true;

    if (state.activeSource !== null) {
      fadeOut(state.activeSource);
      state.activeSource = null;
    }

    loadBuffer(track).then(buffer => {
      if (buffer === null) {
        return;
      }

      if (state.currentTrackId !== track.id) {
        return;
      }

      const active = createSource(buffer, track);
      state.activeSource = active;

      active.source.start();
      fadeIn(active);

      active.source.onended = (): void => {
        if (state.activeSource === active) {
          state.activeSource = null;
          state.isPlaying = false;
        }
      };
    }).catch(() => {
      // Load failed silently
    });
  }

  function pause(): void {
    state.isPlaying = false;
    if (state.activeSource !== null) {
      state.activeSource.source.stop();
      state.activeSource = null;
    }
    for (const fading of state.fadingOutSources) {
      fading.source.stop();
    }
    state.fadingOutSources = [];
  }

  function resume(): void {
    // Web Audio API does not support resume of stopped sources
    // Must replay from beginning
    state.isPlaying = true;
  }

  function setVolume(volume: number): void {
    state.volume = Math.max(0, Math.min(1, volume));
    if (state.activeSource !== null) {
      state.activeSource.gain.gain.value = calculateVolume(state.activeSource.track.volume);
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

/** Test hooks for internal functions. */
export const _test_hooks = {
  createAudioPlayer,
  FADE_DURATION,
};
