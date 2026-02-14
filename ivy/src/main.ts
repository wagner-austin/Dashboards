// Frame lists for each animation
const ANIMATIONS: Record<string, { element: string; folder: string; frames: string[]; delay: number }> = {
  "ivy-1": {
    element: "ivy-1",
    folder: "Ivy_1",
    frames: ["IMG_0704.JPG", "IMG_0705.JPG", "IMG_0706.JPG", "IMG_0707.JPG", "IMG_0708.JPG", "IMG_0709.JPG", "IMG_0710.JPG"],
    delay: 150,
  },
  "ivy-2": {
    element: "ivy-2",
    folder: "Ivy_2",
    frames: ["IMG_2115.JPG", "IMG_2116.JPG", "IMG_2117.JPG", "IMG_2118.JPG", "IMG_2119.JPG", "IMG_2120.JPG", "IMG_2121.JPG", "IMG_2122.JPG"],
    delay: 150,
  },
  "ivy-3": {
    element: "ivy-3",
    folder: "Ivy_3",
    frames: ["IMG_8753.JPG", "IMG_8754.JPG", "IMG_8755.JPG", "IMG_8756.JPG", "IMG_8757.JPG", "IMG_8758.JPG", "IMG_8759.JPG", "IMG_8760.JPG", "IMG_8761.JPG", "IMG_8762.JPG", "IMG_8763.JPG", "IMG_8764.JPG", "IMG_8765.JPG", "IMG_8766.JPG"],
    delay: 120,
  },
  "ivy-4": {
    element: "ivy-4",
    folder: "Ivy_4",
    frames: ["IMG_7795.JPG", "IMG_7796.JPG", "IMG_7797.JPG", "IMG_7798.JPG", "IMG_7799.JPG", "IMG_7800.JPG", "IMG_7801.JPG", "IMG_7802.JPG", "IMG_7803.JPG", "IMG_7804.JPG"],
    delay: 140,
  },
  "ivy-5": {
    element: "ivy-5",
    folder: "Ivy_5",
    frames: ["IMG_7747.JPG", "IMG_7748.JPG", "IMG_7749.JPG", "IMG_7750.JPG", "IMG_7751.JPG", "IMG_7752.JPG"],
    delay: 180,
  },
  "ivy-6": {
    element: "ivy-6",
    folder: "Ivy_6",
    frames: ["IMG_4890.JPG", "IMG_4891.JPG", "IMG_4892.JPG", "IMG_4893.JPG", "IMG_4894.JPG", "IMG_4895.JPG", "IMG_4896.JPG", "IMG_4897.JPG", "IMG_4898.JPG", "IMG_4899.JPG", "IMG_4900.JPG", "IMG_4901.JPG", "IMG_4902.JPG", "IMG_4903.JPG", "IMG_4904.JPG", "IMG_4905.JPG", "IMG_4906.JPG", "IMG_4907.JPG", "IMG_4908.JPG", "IMG_4909.JPG", "IMG_4910.JPG", "IMG_4911.JPG", "IMG_4912.JPG", "IMG_4913.JPG", "IMG_4914.JPG", "IMG_4915.JPG", "IMG_4916.JPG", "IMG_4917.JPG", "IMG_4918.JPG", "IMG_4919.JPG", "IMG_4920.JPG", "IMG_4921.JPG", "IMG_4922.JPG", "IMG_4923.JPG", "IMG_4924.JPG", "IMG_4925.JPG", "IMG_4926.JPG", "IMG_4927.JPG"],
    delay: 80,
  },
  "ivy-7": {
    element: "ivy-7",
    folder: "Ivy_7",
    frames: ["IMG_4125.JPG", "IMG_4126.JPG", "IMG_4127.JPG", "IMG_4128.JPG", "IMG_4129.JPG", "IMG_4130.JPG", "IMG_4131.JPG", "IMG_4132.JPG", "IMG_4133.JPG", "IMG_4134.JPG", "IMG_4135.JPG", "IMG_4136.JPG", "IMG_4137.JPG", "IMG_4138.JPG"],
    delay: 120,
  },
  "teddy-1": {
    element: "teddy-1",
    folder: "Teddy_1",
    frames: ["IMG_5271.JPG", "IMG_5272.JPG", "IMG_5279.JPG", "IMG_5280.JPG", "IMG_5281.JPG", "IMG_5282.JPG", "IMG_5283.JPG", "IMG_5284.JPG", "IMG_5285.JPG"],
    delay: 160,
  },
  "teddy-2": {
    element: "teddy-2",
    folder: "Teddy_2",
    frames: ["IMG_5261.JPG", "IMG_5262.JPG", "IMG_5263.JPG", "IMG_5264.JPG", "IMG_5265.JPG"],
    delay: 200,
  },
};

// Background frames (100 frames)
const BG_FRAMES: string[] = [];
for (let i = 1; i <= 100; i++) {
  BG_FRAMES.push(`frame_${String(i).padStart(3, "0")}.jpg`);
}

// I love you frames (26 frames)
const ILOVEYOU_FRAMES: string[] = [];
for (let i = 1; i <= 26; i++) {
  ILOVEYOU_FRAMES.push(`frame_${String(i).padStart(3, "0")}.png`);
}

function initCharacter(id: string): void {
  const config = ANIMATIONS[id];
  if (!config) return;

  const element = document.getElementById(id) as HTMLImageElement;
  if (!element) return;

  let frameIndex = 0;

  function animate(): void {
    element.src = `./originals/${config.folder}/${config.frames[frameIndex]}`;
    frameIndex = (frameIndex + 1) % config.frames.length;
  }

  // Squish on click
  element.addEventListener("click", (e) => {
    e.stopPropagation();
    element.style.transition = "transform 0.1s ease-out";
    element.style.transform = "scale(0.92)";
    setTimeout(() => {
      element.style.transform = "";
    }, 100);
  });

  animate();
  setInterval(animate, config.delay);
}

function initBackground(): void {
  const bg = document.getElementById("background") as HTMLImageElement;
  if (!bg) return;

  let frameIndex = 0;
  let direction = 1;

  function animate(): void {
    bg.src = `./originals/background_frames/${BG_FRAMES[frameIndex]}`;

    if (direction === 1 && frameIndex >= BG_FRAMES.length - 1) {
      direction = -1;
    } else if (direction === -1 && frameIndex <= 0) {
      direction = 1;
    }
    frameIndex += direction;
  }

  animate();
  setInterval(animate, 100);
}

function initIloveyou(): void {
  const el = document.getElementById("iloveyou") as HTMLImageElement;
  if (!el) return;

  let frameIndex = 0;

  function animate(): void {
    el.src = `./originals/iloveyou_frames/${ILOVEYOU_FRAMES[frameIndex]}`;
    frameIndex = (frameIndex + 1) % ILOVEYOU_FRAMES.length;
  }

  animate();
  setInterval(animate, 100);
}

function initAudio(): void {
  const audio = document.getElementById("audio") as HTMLAudioElement;
  const overlay = document.getElementById("start-overlay");
  const nowPlaying = document.getElementById("now-playing");
  const usVideo = document.getElementById("us-video") as HTMLVideoElement;

  if (!audio || !overlay) return;

  const tracks = [
    { src: "./audio/An Unusual PrinceOnce Upon a Dream (From Sleeping Beauty).mp3", name: "Once Upon a Dream", volume: 0.8 },
    { src: "./audio/Fairies said goodbye to Gruff  Ending scene  TinkerBell And The Legend Of The Neverbeast.mp3", name: "Fairies & Gruff", volume: 0.8 },
    { src: "./audio/To the Fairies They Draw Near.mp3", name: "To the Fairies They Draw Near", volume: 0.8 },
  ];
  let currentTrack = 0;

  function updateNowPlaying(): void {
    if (nowPlaying) {
      nowPlaying.textContent = tracks[currentTrack].name;
    }
  }

  function playTrack(index: number): void {
    audio.src = tracks[index].src;
    audio.volume = tracks[index].volume;
    audio.play();
    updateNowPlaying();
  }

  function nextTrack(): void {
    currentTrack = (currentTrack + 1) % tracks.length;
    playTrack(currentTrack);
  }

  audio.addEventListener("ended", nextTrack);

  overlay.addEventListener("click", () => {
    overlay.classList.add("hidden");
    playTrack(currentTrack);
    if (usVideo) usVideo.play();
  });

  // Keyboard controls
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") {
      nextTrack();
    } else if (e.key === "l" || e.key === "L") {
      audio.loop = !audio.loop;
      nowPlaying?.classList.toggle("looping", audio.loop);
    } else if (e.key === "ArrowLeft") {
      currentTrack = (currentTrack - 1 + tracks.length) % tracks.length;
      playTrack(currentTrack);
    }
  });

  // Swipe controls
  let touchStartX = 0;
  document.addEventListener("touchstart", (e) => {
    touchStartX = e.touches[0].clientX;
  });
  document.addEventListener("touchend", (e) => {
    const deltaX = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(deltaX) > 100) {
      if (deltaX < 0) nextTrack();
      else {
        currentTrack = (currentTrack - 1 + tracks.length) % tracks.length;
        playTrack(currentTrack);
      }
    }
  });
}

function init(): void {
  initAudio();
  initBackground();
  initIloveyou();

  // Init all character animations
  for (const id of Object.keys(ANIMATIONS)) {
    initCharacter(id);
  }
}

document.addEventListener("DOMContentLoaded", init);

export {};
