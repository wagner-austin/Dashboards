import { frames as bridgeFrames } from "./sprites/bridge/w400.js";
import { frames as happyBirthdayFrames } from "./sprites/happy_birthday/w160.js";
// Bothered animation - triggered by click/touch (uses FAST_FRAME_DELAY)
const BOTHERED_ANIMATION = {
    folder: "amanda_bothered",
    frames: [
        "frame_00_delay-0.4s.png",
        "frame_01_delay-0.4s.png",
        "frame_02_delay-0.4s.png",
    ],
    pingPong: true,
    weight: 0,
    isInterrupt: true,
};
const ANIMATIONS = [
    {
        folder: "amanda_reading_looking_down_idle",
        frames: [
            "frame_0_delay-0.4s.png",
            "frame_02_delay-0.4s.png",
            "frame_019_delay-0.4s.png",
        ],
        weight: 65, // Head down reading - most common
        speedMultiplier: 2, // Half speed
        isDefault: true,
    },
    {
        folder: "amanda_reading_looking_up_idle",
        frames: [
            "frame_00_delay-0.4s.png",
            "frame_01_delay-0.4s.png",
        ],
        weight: 20, // Look up
        speedMultiplier: 2, // Half speed
    },
    {
        folder: "amanda_reading_looking_down_page_turn",
        frames: [
            "frame_01_delay-0.4s.png",
            "frame_03_delay-0.4s.png",
            "frame_04_delay-0.4s.png",
            "frame_05_delay-0.4s.png",
        ],
        weight: 10, // Page turn
    },
    {
        folder: "amanda_standing_closes_book",
        frames: [
            "frame_000_delay-0.4s.png",
            "frame_003_delay-0.4s.png",
            "frame_006_delay-0.4s.png",
            "frame_009_delay-0.4s.png",
            "frame_010_delay-0.4s.png",
        ],
        pingPong: true,
        weight: 5, // Standing closes book - rare
    },
];
const DEFAULT_ANIMATION = ANIMATIONS.find((a) => a.isDefault) ?? ANIMATIONS[0];
const OTHER_ANIMATIONS = ANIMATIONS.filter((a) => !a.isDefault);
// Frame delays in ms
const FRAME_DELAY = 600;
const FAST_FRAME_DELAY = 150; // For bothered animation
// Background animation speed
const BG_FRAME_DELAY = 150; // ~6-7fps for background
function pickWeightedAnimation() {
    const totalWeight = OTHER_ANIMATIONS.reduce((sum, a) => sum + a.weight, 0);
    let random = Math.random() * totalWeight;
    for (const animation of OTHER_ANIMATIONS) {
        random -= animation.weight;
        if (random <= 0) {
            return animation;
        }
    }
    return OTHER_ANIMATIONS[0];
}
function initBackground() {
    const background = document.getElementById("background");
    if (!background)
        return;
    let frameIndex = 0;
    let direction = 1; // 1 = forward, -1 = reverse (ping-pong)
    function animate() {
        background.textContent = bridgeFrames[frameIndex];
        // Ping-pong at ends
        if (direction === 1 && frameIndex >= bridgeFrames.length - 1) {
            direction = -1;
        }
        else if (direction === -1 && frameIndex <= 0) {
            direction = 1;
        }
        frameIndex += direction;
    }
    animate();
    setInterval(animate, BG_FRAME_DELAY);
}
function initCharacter() {
    const character = document.getElementById("character");
    if (!character) {
        console.error("Missing character element");
        return;
    }
    let currentAnimation = DEFAULT_ANIMATION;
    let frameIndex = 0;
    let loopCount = 0;
    let direction = 1; // 1 = forward, -1 = reverse (for ping-pong)
    let pauseFrames = 0; // Pause counter for end frame delay
    let animationInterval = null;
    const LOOPS_BEFORE_SWITCH = 3;
    const END_FRAME_PAUSE = 3; // Number of frames to pause at end
    function getFrameDelay() {
        if (currentAnimation.isInterrupt)
            return FAST_FRAME_DELAY;
        const multiplier = currentAnimation.speedMultiplier ?? 1;
        return FRAME_DELAY * multiplier;
    }
    function startTimer() {
        if (animationInterval)
            clearInterval(animationInterval);
        animationInterval = setInterval(animate, getFrameDelay());
    }
    function switchAnimation() {
        const wasInterrupt = currentAnimation.isInterrupt;
        loopCount = 0;
        direction = 1;
        frameIndex = 0;
        // If returning from interrupt, go back to default
        if (wasInterrupt) {
            currentAnimation = DEFAULT_ANIMATION;
        }
        else if (currentAnimation.isDefault) {
            currentAnimation = pickWeightedAnimation();
        }
        else {
            currentAnimation = DEFAULT_ANIMATION;
        }
        // Restart timer with new speed
        startTimer();
    }
    function triggerBothered() {
        // Don't interrupt if already bothered
        if (currentAnimation.isInterrupt)
            return;
        // Tiny squish effect
        character.style.transition = "transform 0.08s ease-out";
        character.style.transform = "translateX(50%) scaleY(0.95) scaleX(1.03)";
        setTimeout(() => {
            character.style.transform = "translateX(50%)";
        }, 80);
        currentAnimation = BOTHERED_ANIMATION;
        frameIndex = 0;
        direction = 1;
        loopCount = 0;
        pauseFrames = 0;
        // Restart timer with fast speed
        startTimer();
    }
    // Click/touch to trigger bothered animation
    character.addEventListener("click", (e) => {
        e.stopPropagation();
        triggerBothered();
    });
    character.addEventListener("touchstart", (e) => {
        e.stopPropagation();
        triggerBothered();
    });
    character.style.cursor = "pointer";
    function animate() {
        const framePath = `./originals/${currentAnimation.folder}/${currentAnimation.frames[frameIndex]}`;
        character.src = framePath;
        // Handle pause at end frame
        if (pauseFrames > 0) {
            pauseFrames--;
            return;
        }
        frameIndex += direction;
        // Handle ping-pong animations
        if (currentAnimation.pingPong) {
            if (frameIndex >= currentAnimation.frames.length) {
                direction = -1;
                frameIndex = currentAnimation.frames.length - 1;
                pauseFrames = END_FRAME_PAUSE;
            }
            else if (frameIndex < 0) {
                direction = 1;
                frameIndex = 0;
                pauseFrames = END_FRAME_PAUSE;
                loopCount++;
            }
        }
        else {
            // Normal loop
            if (frameIndex >= currentAnimation.frames.length) {
                frameIndex = 0;
                loopCount++;
            }
        }
        // Switch animation after a few loops (interrupt animations only play once)
        const loopsNeeded = currentAnimation.isInterrupt ? 1 : LOOPS_BEFORE_SWITCH;
        if (loopCount >= loopsNeeded) {
            switchAnimation();
        }
    }
    // Start animation
    animate();
    startTimer();
}
function initHappyBirthday() {
    const happyBirthday = document.getElementById("happy-birthday");
    if (!happyBirthday)
        return;
    let frameIndex = 0;
    function animate() {
        happyBirthday.textContent = happyBirthdayFrames[frameIndex];
        frameIndex = (frameIndex + 1) % happyBirthdayFrames.length;
    }
    animate();
    setInterval(animate, 80); // ~12fps for the GIF
}
function initAudio() {
    const audio = document.getElementById("audio");
    const overlay = document.getElementById("start-overlay");
    if (!audio || !overlay)
        return;
    const tracks = [
        "./audio/Amanda Tang - Concertino for Clarinet in Eb major.mp3",
        "./audio/peace_dancer.mp3",
    ];
    let currentTrack = 0;
    audio.addEventListener("ended", () => {
        currentTrack = (currentTrack + 1) % tracks.length;
        audio.src = tracks[currentTrack];
        audio.play();
    });
    overlay.addEventListener("click", () => {
        overlay.classList.add("hidden");
        audio.volume = 0.4;
        audio.src = tracks[currentTrack];
        audio.play();
    });
}
function init() {
    initAudio();
    initBackground();
    initHappyBirthday();
    initCharacter();
}
document.addEventListener("DOMContentLoaded", init);
