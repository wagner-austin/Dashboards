/**
 * Validation functions for audio configuration.
 * Uses require_* pattern for strict TypedDict validation.
 */

import type { AudioTrack, AudioConfig, TrackTags, TimeOfDay } from "./types.js";

/** Type guard for checking if value is a record */
function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Type guard for TimeOfDay */
function isTimeOfDay(value: unknown): value is TimeOfDay {
  return value === "day" || value === "night" || value === "dawn" || value === "dusk";
}

/** Type guard for TrackTags */
function isTrackTags(value: unknown): value is TrackTags {
  if (!isRecord(value)) return false;

  const time = value.time;
  if (time !== undefined && !isTimeOfDay(time)) return false;

  const location = value.location;
  if (location !== undefined && typeof location !== "string") return false;

  return true;
}

/**
 * Require valid AudioTrack from config.
 * Throws descriptive error if invalid.
 */
function requireAudioTrack(value: unknown, index: number): AudioTrack {
  if (!isRecord(value)) {
    throw new Error(`audio.tracks[${String(index)}]: must be an object`);
  }

  const id = value.id;
  if (typeof id !== "string" || id.length === 0) {
    throw new Error(`audio.tracks[${String(index)}]: missing or invalid "id" field`);
  }

  const path = value.path;
  if (typeof path !== "string" || path.length === 0) {
    throw new Error(`audio.tracks[${String(index)}] "${id}": missing or invalid "path" field`);
  }

  const volume = value.volume;
  if (typeof volume !== "number" || volume < 0 || volume > 1) {
    throw new Error(`audio.tracks[${String(index)}] "${id}": "volume" must be a number between 0 and 1`);
  }

  const loop = value.loop;
  if (typeof loop !== "boolean") {
    throw new Error(`audio.tracks[${String(index)}] "${id}": "loop" must be a boolean`);
  }

  const tags = value.tags;
  if (!isTrackTags(tags)) {
    throw new Error(`audio.tracks[${String(index)}] "${id}": "tags" must be a valid TrackTags object`);
  }

  // Build validated track
  const validatedTags: TrackTags = {
    ...(tags.time !== undefined ? { time: tags.time } : {}),
    ...(tags.location !== undefined ? { location: tags.location } : {}),
  };

  return {
    id,
    path,
    volume,
    loop,
    tags: validatedTags,
  };
}

/**
 * Validate entire audio configuration from config.json.
 * Throws descriptive error if invalid.
 */
export function validateAudioConfig(config: unknown): AudioConfig {
  if (!isRecord(config)) {
    throw new Error("audio: must be an object");
  }

  const enabled = config.enabled;
  if (typeof enabled !== "boolean") {
    throw new Error('audio: "enabled" must be a boolean');
  }

  const masterVolume = config.masterVolume;
  if (typeof masterVolume !== "number" || masterVolume < 0 || masterVolume > 1) {
    throw new Error('audio: "masterVolume" must be a number between 0 and 1');
  }

  const tracks = config.tracks;
  if (!Array.isArray(tracks)) {
    throw new Error('audio: "tracks" must be an array');
  }

  const validatedTracks: AudioTrack[] = [];
  const ids = new Set<string>();

  for (let i = 0; i < tracks.length; i++) {
    const track = requireAudioTrack(tracks[i], i);

    if (ids.has(track.id)) {
      throw new Error(`audio.tracks[${String(i)}]: duplicate track id "${track.id}"`);
    }
    ids.add(track.id);

    validatedTracks.push(track);
  }

  return {
    enabled,
    masterVolume,
    tracks: validatedTracks,
  };
}

/** Test hooks for internal functions */
export const _test_hooks = {
  isRecord,
  isTimeOfDay,
  isTrackTags,
  requireAudioTrack,
};
