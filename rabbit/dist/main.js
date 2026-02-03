/**
 * Main entry point for the ASCII animation engine.
 * Full viewport, world scrolling, frame-based animations.
 */
// ============================================================================
// Ground tile pattern (static, scrolls with world)
// ============================================================================
const GROUND_TILE = [
    "                                                            ",
    "      .                  .                .                 ",
    "  .       .      +           .       .          .     +     ",
    "     .        .      .   +       .        .  +      .    .  ",
    " .      + .      .  .      . .      +  .      .   .     .   ",
    "   . .     .  +    .   . .    .  .     . +     . .   +   .  ",
];
function measureViewport(screen) {
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;
    // Measure actual character size
    screen.textContent = "X";
    const rect = screen.getBoundingClientRect();
    const charW = rect.width;
    const charH = rect.height;
    screen.textContent = "";
    return {
        width: Math.floor(vw / charW),
        height: Math.floor(vh / charH),
        charW,
        charH,
    };
}
function createBuffer(width, height) {
    return Array.from({ length: height }, () => Array(width).fill(" "));
}
function renderBuffer(buffer) {
    return buffer.map((row) => row.join("")).join("\n");
}
// ============================================================================
// Drawing Functions
// ============================================================================
function drawSprite(buffer, lines, x, y, width, height) {
    for (let i = 0; i < lines.length; i++) {
        const row = y + i;
        const line = lines[i];
        if (line === undefined)
            continue;
        if (row >= 0 && row < height) {
            for (let j = 0; j < line.length; j++) {
                const col = x + j;
                const ch = line[j];
                if (col >= 0 && col < width && ch !== undefined && ch !== " ") {
                    const bufferRow = buffer[row];
                    if (bufferRow !== undefined) {
                        bufferRow[col] = ch;
                    }
                }
            }
        }
    }
}
function drawGround(buffer, offsetX, width, height) {
    const tileWidth = GROUND_TILE[0]?.length ?? 60;
    for (let i = 0; i < GROUND_TILE.length; i++) {
        const row = height - GROUND_TILE.length + i;
        const tileLine = GROUND_TILE[i];
        if (row >= 0 && row < height && tileLine !== undefined) {
            const bufferRow = buffer[row];
            if (bufferRow === undefined)
                continue;
            for (let col = 0; col < width; col++) {
                const srcCol = ((col - Math.floor(offsetX)) % tileWidth + tileWidth) % tileWidth;
                const ch = tileLine[srcCol];
                if (ch !== undefined && ch !== " ") {
                    bufferRow[col] = ch;
                }
            }
        }
    }
}
// ============================================================================
// Sprite Loading
// ============================================================================
async function loadSpriteFrames(spriteName, animationName, width, direction) {
    const suffix = direction !== undefined ? `_${direction}` : "";
    const module = (await import(`./sprites/${spriteName}/${animationName}/w${String(width)}${suffix}.js`));
    return {
        width,
        frames: module.frames,
    };
}
async function loadStaticSpriteFrames(spriteName, width) {
    const module = (await import(`./sprites/${spriteName}/w${String(width)}.js`));
    return {
        width,
        frames: module.frames,
    };
}
async function loadConfig() {
    const response = await fetch("./config.json");
    return (await response.json());
}
function createAnimationTimer(intervalMs, onTick) {
    let id = null;
    return {
        start() {
            if (id !== null)
                return;
            id = setInterval(onTick, intervalMs);
        },
        stop() {
            if (id !== null) {
                clearInterval(id);
                id = null;
            }
        },
        isRunning() {
            return id !== null;
        },
    };
}
// ============================================================================
// Main Application
// ============================================================================
async function init() {
    const config = await loadConfig();
    const screenEl = document.getElementById("screen");
    if (screenEl === null) {
        throw new Error("Screen element not found");
    }
    // Store as non-null HTMLPreElement for use in closures
    const screen = screenEl;
    // Measure viewport
    const viewport = measureViewport(screen);
    console.log("viewport:", document.documentElement.clientWidth, "x", document.documentElement.clientHeight, "buffer:", viewport.width, "x", viewport.height);
    // Load bunny sprites
    const bunnyConfig = config.sprites.bunny;
    if (bunnyConfig?.animations === undefined) {
        throw new Error("Bunny sprite config not found");
    }
    // Load walk animation (both directions)
    const walkConfig = bunnyConfig.animations.walk;
    let bunnyWalkFramesLeft = [];
    let bunnyWalkFramesRight = [];
    if (walkConfig !== undefined) {
        const walkLeftSet = await loadSpriteFrames("bunny", "walk", 50, "left");
        const walkRightSet = await loadSpriteFrames("bunny", "walk", 50, "right");
        bunnyWalkFramesLeft = walkLeftSet.frames;
        bunnyWalkFramesRight = walkRightSet.frames;
    }
    // Load jump animation (both directions)
    const jumpConfig = bunnyConfig.animations.jump;
    let bunnyJumpFramesLeft = [];
    let bunnyJumpFramesRight = [];
    if (jumpConfig !== undefined) {
        const jumpLeftSet = await loadSpriteFrames("bunny", "jump", 50, "left");
        const jumpRightSet = await loadSpriteFrames("bunny", "jump", 50, "right");
        bunnyJumpFramesLeft = jumpLeftSet.frames;
        bunnyJumpFramesRight = jumpRightSet.frames;
    }
    // Load tree sprite
    const treeConfig = config.sprites.tree;
    let treeFrames = [];
    if (treeConfig?.widths !== undefined) {
        const treeSet = await loadStaticSpriteFrames("tree", 120);
        treeFrames = treeSet.frames;
    }
    // Initialize game state
    const state = {
        viewport,
        facingRight: false,
        bunnyFrameIdx: 0,
        isJumping: false,
        jumpFrameIdx: 0,
        treeX: viewport.width, // Tree starts off-screen right, scrolls into view
        treeFrameIdx: 0,
        treeDirection: 1,
        bunnyWalkFramesLeft,
        bunnyWalkFramesRight,
        bunnyJumpFramesLeft,
        bunnyJumpFramesRight,
        treeFrames,
    };
    // Animation timing constants (in ms)
    const WALK_INTERVAL = 120;
    const TREE_INTERVAL = 250;
    const JUMP_INTERVAL = 58;
    // Scroll speed from config (characters per second)
    const SCROLL_SPEED = config.settings.scrollSpeed;
    // Walk animation timer (runs continuously)
    const walkTimer = createAnimationTimer(WALK_INTERVAL, () => {
        if (!state.isJumping) {
            const walkFrames = state.facingRight
                ? state.bunnyWalkFramesRight
                : state.bunnyWalkFramesLeft;
            state.bunnyFrameIdx = (state.bunnyFrameIdx + 1) % walkFrames.length;
        }
    });
    // Tree animation timer (ping-pong, runs continuously)
    const treeTimer = createAnimationTimer(TREE_INTERVAL, () => {
        state.treeFrameIdx += state.treeDirection;
        if (state.treeFrameIdx >= state.treeFrames.length) {
            state.treeFrameIdx = state.treeFrames.length - 2;
            state.treeDirection = -1;
        }
        else if (state.treeFrameIdx < 0) {
            state.treeFrameIdx = 1;
            state.treeDirection = 1;
        }
    });
    // Jump animation timer (starts on spacebar, stops when complete)
    const jumpTimer = createAnimationTimer(JUMP_INTERVAL, () => {
        const jumpFrames = state.facingRight
            ? state.bunnyJumpFramesRight
            : state.bunnyJumpFramesLeft;
        state.jumpFrameIdx++;
        if (state.jumpFrameIdx >= jumpFrames.length) {
            state.isJumping = false;
            state.jumpFrameIdx = 0;
            jumpTimer.stop();
        }
    });
    // Handle resize
    window.addEventListener("resize", () => {
        state.viewport = measureViewport(screen);
    });
    // Keyboard controls
    document.addEventListener("keydown", (e) => {
        if (e.key === "ArrowLeft" || e.key === "a") {
            state.facingRight = false;
        }
        else if (e.key === "ArrowRight" || e.key === "d") {
            state.facingRight = true;
        }
        else if (e.key === " " && !state.isJumping) {
            state.isJumping = true;
            state.jumpFrameIdx = 0;
            jumpTimer.start();
            e.preventDefault();
        }
        else if (e.key === "r") {
            state.treeX = state.viewport.width;
        }
    });
    // Render loop (uses delta time for frame-rate independent movement)
    let lastTime = 0;
    function render(currentTime) {
        // Calculate delta time in seconds
        const deltaTime = lastTime > 0 ? (currentTime - lastTime) / 1000 : 0;
        lastTime = currentTime;
        const { width, height } = state.viewport;
        // Create fresh buffer
        const buffer = createBuffer(width, height);
        // Draw ground (scrolls with tree)
        drawGround(buffer, state.treeX, width, height);
        // Draw tree
        const treeFrame = state.treeFrames[state.treeFrameIdx];
        if (treeFrame !== undefined) {
            const treeLines = treeFrame.split("\n");
            const treeY = height - treeLines.length;
            drawSprite(buffer, treeLines, Math.floor(state.treeX), treeY, width, height);
        }
        // Draw bunny
        const bunnyFrames = state.isJumping
            ? (state.facingRight ? state.bunnyJumpFramesRight : state.bunnyJumpFramesLeft)
            : (state.facingRight ? state.bunnyWalkFramesRight : state.bunnyWalkFramesLeft);
        const frameIdx = state.isJumping ? state.jumpFrameIdx : state.bunnyFrameIdx;
        const frame = bunnyFrames[frameIdx];
        const bunnyLines = frame !== undefined ? frame.split("\n") : [];
        const bunnyX = Math.floor(width / 2) - 20;
        const bunnyY = height - bunnyLines.length - 2;
        drawSprite(buffer, bunnyLines, bunnyX, bunnyY, width, height);
        // Render to screen
        screen.textContent = renderBuffer(buffer);
        // Update scroll position using delta time (frame-rate independent)
        const TREE_WIDTH = 130;
        const scrollAmount = SCROLL_SPEED * deltaTime;
        if (state.facingRight) {
            state.treeX -= scrollAmount;
            if (state.treeX < -TREE_WIDTH) {
                state.treeX = width;
            }
        }
        else {
            state.treeX += scrollAmount;
            if (state.treeX > width) {
                state.treeX = -TREE_WIDTH;
            }
        }
        // Schedule next frame (requestAnimationFrame for smooth rendering)
        requestAnimationFrame(render);
    }
    // Start animation timers
    walkTimer.start();
    treeTimer.start();
    // Start render loop with requestAnimationFrame
    requestAnimationFrame(render);
}
// Start the application
init().catch((error) => {
    console.error("Failed to initialize:", error);
});
export {};
//# sourceMappingURL=main.js.map