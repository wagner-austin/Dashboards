/**
 * Audio player with dependency injection for testability.
 * Uses HTMLAudioElement for cross-browser compatibility.
 * Supports fade-in on start and crossfade between tracks.
 */
/** Default fade duration in milliseconds */
const FADE_DURATION_MS = 1000;
const FADE_STEPS = 20;
/**
 * Create audio player with injected dependencies.
 * Allows testing without actual Audio elements.
 */
export function createAudioPlayer(deps) {
    const state = {
        currentTrackId: null,
        currentTrack: null,
        isPlaying: false,
        volume: deps.masterVolume,
        element: null,
        fadeIn: null,
        fadeOuts: [],
    };
    function calculateVolume(trackVolume) {
        return state.volume * trackVolume;
    }
    function stopFadeIn() {
        if (state.fadeIn !== null) {
            clearInterval(state.fadeIn.interval);
            state.fadeIn = null;
        }
    }
    function removeFadeOutByInterval(interval) {
        clearInterval(interval);
        state.fadeOuts = state.fadeOuts.filter(f => f.interval !== interval);
    }
    function stopAllFadeOuts() {
        for (const fadeOp of state.fadeOuts) {
            clearInterval(fadeOp.interval);
        }
        state.fadeOuts = [];
    }
    function fadeIn(element, targetVolume) {
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
    function fadeOut(element, startVolume) {
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
    function play(track) {
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
    function pause() {
        stopFadeIn();
        stopAllFadeOuts();
        if (state.element !== null) {
            state.element.pause();
        }
        state.isPlaying = false;
    }
    function resume() {
        if (state.element !== null && !state.isPlaying) {
            state.isPlaying = true;
            state.element.play().catch(() => {
                // May fail if not resumed from user interaction
            });
        }
    }
    function setVolume(volume) {
        // Clamp volume to valid range
        const clampedVolume = Math.max(0, Math.min(1, volume));
        state.volume = clampedVolume;
        // Update element volume if playing
        if (state.element !== null && state.currentTrack !== null) {
            state.element.volume = calculateVolume(state.currentTrack.volume);
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
/** Test hooks for internal functions */
export const _test_hooks = {
    createAudioPlayer,
};
//# sourceMappingURL=AudioPlayer.js.map