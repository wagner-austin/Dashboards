/**
 * Audio player using Web Audio API.
 * Fetches audio as ArrayBuffer, decodes to AudioBuffer, plays via BufferSourceNode.
 * Supports crossfade between tracks using GainNode ramping.
 */
/** Fade duration in seconds. */
const FADE_DURATION = 1.0;
/**
 * Create audio player with Web Audio API.
 *
 * Args:
 *     deps: Audio player dependencies.
 *
 * Returns:
 *     AudioPlayer instance.
 */
export function createAudioPlayer(deps) {
    const state = {
        currentTrackId: null,
        isPlaying: false,
        volume: deps.masterVolume,
        buffers: new Map(),
        activeSource: null,
        fadingOutSources: [],
    };
    function calculateVolume(trackVolume) {
        return state.volume * trackVolume;
    }
    async function loadBuffer(track) {
        const cached = state.buffers.get(track.id);
        if (cached !== undefined) {
            console.log("[AudioPlayer] Using cached buffer for:", track.id);
            return cached;
        }
        console.log("[AudioPlayer] Fetching audio:", track.path);
        const response = await deps.fetchFn(track.path);
        if (!response.ok) {
            console.log("[AudioPlayer] Fetch failed:", response.status);
            return null;
        }
        console.log("[AudioPlayer] Decoding audio...");
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await deps.context.decodeAudioData(arrayBuffer);
        state.buffers.set(track.id, audioBuffer);
        console.log("[AudioPlayer] Audio decoded and cached:", track.id);
        return audioBuffer;
    }
    function fadeOut(active) {
        const currentTime = 0;
        active.gain.gain.linearRampToValueAtTime(0, currentTime + FADE_DURATION);
        state.fadingOutSources.push(active);
        setTimeout(() => {
            active.source.stop();
            state.fadingOutSources = state.fadingOutSources.filter(s => s !== active);
        }, FADE_DURATION * 1000);
    }
    function createSource(buffer, track) {
        const source = deps.context.createBufferSource();
        source.buffer = buffer;
        source.loop = track.loop;
        const gain = deps.context.createGain();
        gain.gain.value = 0;
        source.connect(gain);
        gain.connect(deps.context.destination);
        return { source, gain, track };
    }
    function fadeIn(active) {
        const targetVolume = calculateVolume(active.track.volume);
        const currentTime = 0;
        active.gain.gain.linearRampToValueAtTime(targetVolume, currentTime + FADE_DURATION);
    }
    function play(track) {
        console.log("[AudioPlayer] play() called for:", track.id);
        state.currentTrackId = track.id;
        state.isPlaying = true;
        if (state.activeSource !== null) {
            fadeOut(state.activeSource);
            state.activeSource = null;
        }
        loadBuffer(track).then(buffer => {
            if (buffer === null) {
                console.log("[AudioPlayer] Buffer is null, aborting");
                return;
            }
            if (state.currentTrackId !== track.id) {
                console.log("[AudioPlayer] Track changed, aborting");
                return;
            }
            console.log("[AudioPlayer] Creating source and starting playback");
            const active = createSource(buffer, track);
            state.activeSource = active;
            active.source.start();
            fadeIn(active);
            console.log("[AudioPlayer] Playback started");
            active.source.onended = () => {
                if (state.activeSource === active) {
                    state.activeSource = null;
                    state.isPlaying = false;
                }
            };
        }).catch((err) => {
            console.log("[AudioPlayer] Load failed:", err);
        });
    }
    function pause() {
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
    function resume() {
        // Web Audio API does not support resume of stopped sources
        // Must replay from beginning
        state.isPlaying = true;
    }
    function setVolume(volume) {
        state.volume = Math.max(0, Math.min(1, volume));
        if (state.activeSource !== null) {
            state.activeSource.gain.gain.value = calculateVolume(state.activeSource.track.volume);
        }
    }
    function getState() {
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
//# sourceMappingURL=AudioPlayer.js.map