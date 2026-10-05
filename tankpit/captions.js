// Which caption belongs to the frame a viewer is watching.
//
// The fleet sends each bot's recent captions, oldest first, each stamped with
// the wall-clock moment it became true (`at_ms`, the bot container's clock).
// The video reaches a viewer several seconds after the moment it shows, so
// the newest caption is AHEAD of the picture. The encoder stamps every
// segment with its own wall-clock start on the same clock
// (EXT-X-PROGRAM-DATE-TIME), and the player reports the moment of the frame
// on screen; the caption to show is the last one that was already true then.

/**
 * The caption in force at a moment.
 *
 * @param {Array<{at_ms: number}>} captions Oldest first.
 * @param {number} momentMs Wall-clock epoch milliseconds of the frame shown.
 * @returns {object|null} The last caption at or before the moment, or null
 *   when the bot had not decided anything yet at that moment.
 */
export function captionAt(captions, momentMs) {
  let current = null;
  for (const caption of captions) {
    if (caption.at_ms > momentMs) {
      break;
    }
    current = caption;
  }
  return current;
}

/**
 * The wall-clock moment of the frame a player is showing.
 *
 * Two players, because real devices need both (the page's own note): hls.js
 * on Media Source Extensions reports `playingDate`; native HLS (iOS Safari)
 * reports the stream's start date, and the frame is that plus the playback
 * position.
 *
 * @param {HTMLVideoElement} video The element playing the stream.
 * @param {{playingDate: Date|null}|null} hls The hls.js instance, or null on
 *   a native player.
 * @returns {number|null} Epoch milliseconds, or null before playback has a
 *   dated frame.
 */
export function frameMomentMs(video, hls) {
  if (hls !== null) {
    return hls.playingDate === null ? null : hls.playingDate.getTime();
  }
  if (typeof video.getStartDate !== "function") {
    return null;
  }
  const start = video.getStartDate().getTime();
  return Number.isNaN(start) ? null : start + video.currentTime * 1000;
}
