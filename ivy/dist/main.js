// Get sorted list of JPG files from a folder
function getFrameFiles(folder, count) {
    // Files are named like IMG_XXXX.JPG - we need to return them sorted
    const frames = [];
    for (let i = 0; i < count; i++) {
        frames.push(`frame_${i}.jpg`);
    }
    return frames;
}
// Frame counts for each animation folder
const IVY_ANIMATIONS = [
    { elementId: "ivy-1", folder: "Ivy_1", frameCount: 8, frameDelay: 150 },
    { elementId: "ivy-2", folder: "Ivy_2", frameCount: 8, frameDelay: 150 },
    { elementId: "ivy-3", folder: "Ivy_3", frameCount: 14, frameDelay: 120 },
    { elementId: "ivy-4", folder: "Ivy_4", frameCount: 10, frameDelay: 140 },
    { elementId: "ivy-5", folder: "Ivy_5", frameCount: 6, frameDelay: 180 },
    { elementId: "ivy-6", folder: "Ivy_6", frameCount: 38, frameDelay: 80, pingPong: true },
    { elementId: "ivy-7", folder: "Ivy_7", frameCount: 14, frameDelay: 120 },
];
const TEDDY_ANIMATIONS = [
    { elementId: "teddy-1", folder: "Teddy_1", frameCount: 9, frameDelay: 160 },
    { elementId: "teddy-2", folder: "Teddy_2", frameCount: 5, frameDelay: 200 },
];
// Scan folder and get actual filenames sorted
async function scanFolder(folder) {
    // Since we can't actually scan folders in browser, we'll use known filenames
    // The files are named IMG_XXXX.JPG with sequential numbers
    const response = await fetch(`./originals/${folder}/`);
    if (!response.ok) {
        console.error(`Failed to scan folder ${folder}`);
        return [];
    }
    // Parse directory listing (this works on simple servers)
    const text = await response.text();
    const matches = text.match(/IMG_\d+(?:\s\d+)?\.JPG/gi) || [];
    // Sort by the number in the filename
    return [...new Set(matches)].sort((a, b) => {
        const numA = parseInt(a.match(/\d+/)?.[0] || "0");
        const numB = parseInt(b.match(/\d+/)?.[0] || "0");
        return numA - numB;
    });
}
// Hardcoded frame lists since we know the files
const FRAME_LISTS = {
    Ivy_1: ["IMG_0704.JPG", "IMG_0705.JPG", "IMG_0706.JPG", "IMG_0707.JPG", "IMG_0708.JPG", "IMG_0709.JPG", "IMG_0710.JPG"],
    Ivy_2: ["IMG_2115.JPG", "IMG_2116.JPG", "IMG_2117.JPG", "IMG_2118.JPG", "IMG_2119.JPG", "IMG_2120.JPG", "IMG_2121.JPG", "IMG_2122.JPG"],
    Ivy_3: ["IMG_8753.JPG", "IMG_8754.JPG", "IMG_8755.JPG", "IMG_8756.JPG", "IMG_8757.JPG", "IMG_8758.JPG", "IMG_8759.JPG", "IMG_8760.JPG", "IMG_8761.JPG", "IMG_8762.JPG", "IMG_8763.JPG", "IMG_8764.JPG", "IMG_8765.JPG", "IMG_8766.JPG"],
    Ivy_4: ["IMG_7795.JPG", "IMG_7796.JPG", "IMG_7797.JPG", "IMG_7798.JPG", "IMG_7799.JPG", "IMG_7800.JPG", "IMG_7801.JPG", "IMG_7802.JPG", "IMG_7803.JPG", "IMG_7804.JPG"],
    Ivy_5: ["IMG_7747.JPG", "IMG_7748.JPG", "IMG_7749.JPG", "IMG_7750.JPG", "IMG_7751.JPG", "IMG_7752.JPG"],
    Ivy_6: ["IMG_4890.JPG", "IMG_4891.JPG", "IMG_4892.JPG", "IMG_4893.JPG", "IMG_4894.JPG", "IMG_4895.JPG", "IMG_4896.JPG", "IMG_4897.JPG", "IMG_4898.JPG", "IMG_4899.JPG", "IMG_4900.JPG", "IMG_4901.JPG", "IMG_4902.JPG", "IMG_4903.JPG", "IMG_4904.JPG", "IMG_4905.JPG", "IMG_4906.JPG", "IMG_4907.JPG", "IMG_4908.JPG", "IMG_4909.JPG", "IMG_4910.JPG", "IMG_4911.JPG", "IMG_4912.JPG", "IMG_4913.JPG", "IMG_4914.JPG", "IMG_4915.JPG", "IMG_4916.JPG", "IMG_4917.JPG", "IMG_4918.JPG", "IMG_4919.JPG", "IMG_4920.JPG", "IMG_4921.JPG", "IMG_4922.JPG", "IMG_4923.JPG", "IMG_4924.JPG", "IMG_4925.JPG", "IMG_4926.JPG", "IMG_4927.JPG"],
    Ivy_7: ["IMG_4125.JPG", "IMG_4126.JPG", "IMG_4127.JPG", "IMG_4128.JPG", "IMG_4129.JPG", "IMG_4130.JPG", "IMG_4131.JPG", "IMG_4132.JPG", "IMG_4133.JPG", "IMG_4134.JPG", "IMG_4135.JPG", "IMG_4136.JPG", "IMG_4137.JPG", "IMG_4138.JPG"],
    Teddy_1: ["IMG_5271.JPG", "IMG_5272.JPG", "IMG_5279.JPG", "IMG_5280.JPG", "IMG_5281.JPG", "IMG_5282.JPG", "IMG_5283.JPG", "IMG_5284.JPG", "IMG_5285.JPG"],
    Teddy_2: ["IMG_5261.JPG", "IMG_5262.JPG", "IMG_5263.JPG", "IMG_5264.JPG", "IMG_5265.JPG"],
};
function addSquishEffect(element) {
    const squish = () => {
        element.style.transition = "transform 0.1s ease-out";
        element.style.transform = "scale(0.92)";
        setTimeout(() => {
            element.style.transform = "scale(1)";
        }, 100);
    };
    element.addEventListener("click", (e) => {
        e.stopPropagation();
        squish();
    });
    element.addEventListener("touchstart", (e) => {
        e.stopPropagation();
        squish();
    });
    element.style.cursor = "pointer";
}
function initAnimation(config) {
    const element = document.getElementById(config.elementId);
    if (!element) {
        console.error(`Element not found: ${config.elementId}`);
        return null;
    }
    const frames = FRAME_LISTS[config.folder];
    if (!frames || frames.length === 0) {
        console.error(`No frames for folder: ${config.folder}`);
        return null;
    }
    // Add squish effect on tap
    addSquishEffect(element);
    return {
        config,
        element,
        frames,
        frameIndex: 0,
        direction: 1,
    };
}
function animateElement(state) {
    const framePath = `./originals/${state.config.folder}/${state.frames[state.frameIndex]}`;
    state.element.src = framePath;
    // Advance frame
    state.frameIndex += state.direction;
    // Handle ping-pong or loop
    if (state.config.pingPong) {
        if (state.frameIndex >= state.frames.length) {
            state.direction = -1;
            state.frameIndex = state.frames.length - 2;
        }
        else if (state.frameIndex < 0) {
            state.direction = 1;
            state.frameIndex = 1;
        }
    }
    else {
        // Loop
        if (state.frameIndex >= state.frames.length) {
            state.frameIndex = 0;
        }
    }
}
function initAllAnimations() {
    const allConfigs = [...IVY_ANIMATIONS, ...TEDDY_ANIMATIONS];
    for (const config of allConfigs) {
        const state = initAnimation(config);
        if (state) {
            // Initial frame
            animateElement(state);
            // Start animation loop
            setInterval(() => animateElement(state), config.frameDelay);
        }
    }
}
function initAudio() {
    const audio = document.getElementById("audio");
    const overlay = document.getElementById("start-overlay");
    const nowPlaying = document.getElementById("now-playing");
    if (!audio || !overlay)
        return;
    const tracks = [
        { src: "./audio/An Unusual PrinceOnce Upon a Dream (From Sleeping Beauty).mp3", name: "Once Upon a Dream - Sleeping Beauty", volume: 0.8 },
        { src: "./audio/Fairies said goodbye to Gruff  Ending scene  TinkerBell And The Legend Of The Neverbeast.mp3", name: "Fairies & Gruff - TinkerBell", volume: 0.8 },
        { src: "./audio/To the Fairies They Draw Near.mp3", name: "To the Fairies They Draw Near", volume: 0.8 },
    ];
    let currentTrack = 0;
    function updateNowPlaying() {
        if (nowPlaying) {
            nowPlaying.textContent = tracks[currentTrack].name;
        }
    }
    function playTrack(index) {
        audio.src = tracks[index].src;
        audio.volume = tracks[index].volume;
        audio.play();
        updateNowPlaying();
    }
    function nextTrack() {
        currentTrack = (currentTrack + 1) % tracks.length;
        playTrack(currentTrack);
    }
    audio.addEventListener("ended", nextTrack);
    overlay.addEventListener("click", () => {
        overlay.classList.add("hidden");
        playTrack(currentTrack);
        // Also start videos
        const videos = document.querySelectorAll("video");
        videos.forEach((v) => v.play());
    });
    // Keyboard controls
    document.addEventListener("keydown", (e) => {
        if (e.key === "n" || e.key === "N" || e.key === "ArrowRight") {
            nextTrack();
        }
        else if (e.key === "l" || e.key === "L") {
            audio.loop = !audio.loop;
            nowPlaying?.classList.toggle("looping", audio.loop);
        }
        else if (e.key === "ArrowLeft") {
            currentTrack = (currentTrack - 1 + tracks.length) % tracks.length;
            playTrack(currentTrack);
        }
    });
    // Swipe controls for mobile
    let touchStartX = 0;
    let touchStartY = 0;
    document.addEventListener("touchstart", (e) => {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    });
    document.addEventListener("touchend", (e) => {
        const touchEndX = e.changedTouches[0].clientX;
        const touchEndY = e.changedTouches[0].clientY;
        const deltaX = touchEndX - touchStartX;
        const deltaY = touchEndY - touchStartY;
        // Only trigger if horizontal swipe is dominant and long enough
        if (Math.abs(deltaX) > 100 && Math.abs(deltaX) > Math.abs(deltaY)) {
            if (deltaX < 0) {
                // Swipe left = next track
                nextTrack();
            }
            else {
                // Swipe right = previous track
                currentTrack = (currentTrack - 1 + tracks.length) % tracks.length;
                playTrack(currentTrack);
            }
        }
    });
}
function init() {
    initAudio();
    initAllAnimations();
}
document.addEventListener("DOMContentLoaded", init);
export {};
