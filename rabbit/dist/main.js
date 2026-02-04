/**
 * Main entry point for the ASCII animation engine.
 * Full viewport, world scrolling, frame-based animations.
 */
import { calculateScrollUpdate, updateSpeedTransition } from "./world/Parallax.js";
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
function drawSpriteFade(buffer, oldLines, newLines, oldX, newX, oldY, newY, width, height, progress // 0 = all old, 1 = all new
) {
    // Ease-in curve: prioritize showing new pixels sooner
    // progress^0.5 makes new pixels appear faster
    const easedProgress = Math.pow(progress, 0.5);
    // Draw new sprite first (fading in) - these take priority
    for (let i = 0; i < newLines.length; i++) {
        const row = newY + i;
        const line = newLines[i];
        if (line === undefined)
            continue;
        if (row >= 0 && row < height) {
            for (let j = 0; j < line.length; j++) {
                const col = newX + j;
                const ch = line[j];
                if (col >= 0 && col < width && ch !== undefined && ch !== " ") {
                    // Higher chance to show new pixels (eased progress)
                    if (Math.random() < easedProgress) {
                        const bufferRow = buffer[row];
                        if (bufferRow !== undefined) {
                            bufferRow[col] = ch;
                        }
                    }
                }
            }
        }
    }
    // Draw old sprite (fading out) - only fills gaps
    const inverseEased = 1 - easedProgress;
    for (let i = 0; i < oldLines.length; i++) {
        const row = oldY + i;
        const line = oldLines[i];
        if (line === undefined)
            continue;
        if (row < 0 || row >= height)
            continue;
        const bufferRow = buffer[row];
        if (bufferRow === undefined)
            continue;
        for (let j = 0; j < line.length; j++) {
            const col = oldX + j;
            const ch = line[j];
            if (col >= 0 &&
                col < width &&
                ch !== undefined &&
                ch !== " " &&
                bufferRow[col] === " " &&
                Math.random() < inverseEased) {
                bufferRow[col] = ch;
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
    // Load idle animation (both directions)
    const idleConfig = bunnyConfig.animations.idle;
    let bunnyIdleFramesLeft = [];
    let bunnyIdleFramesRight = [];
    if (idleConfig !== undefined) {
        const idleLeftSet = await loadSpriteFrames("bunny", "idle", 40, "left");
        const idleRightSet = await loadSpriteFrames("bunny", "idle", 40, "right");
        bunnyIdleFramesLeft = idleLeftSet.frames;
        bunnyIdleFramesRight = idleRightSet.frames;
    }
    // Load walk_to_idle transition (both directions)
    const walkToIdleConfig = bunnyConfig.animations.walk_to_idle;
    let bunnyWalkToIdleFramesLeft = [];
    let bunnyWalkToIdleFramesRight = [];
    if (walkToIdleConfig !== undefined) {
        const walkToIdleLeftSet = await loadSpriteFrames("bunny", "walk_to_idle", 40, "left");
        const walkToIdleRightSet = await loadSpriteFrames("bunny", "walk_to_idle", 40, "right");
        bunnyWalkToIdleFramesLeft = walkToIdleLeftSet.frames;
        bunnyWalkToIdleFramesRight = walkToIdleRightSet.frames;
    }
    // Load tree sprite at all sizes
    const treeConfig = config.sprites.tree;
    const treeSizes = [];
    if (treeConfig?.widths !== undefined) {
        const widths = [60, 120, 180];
        for (const w of widths) {
            const treeSet = await loadStaticSpriteFrames("tree", w);
            treeSizes.push({ width: w, frames: treeSet.frames });
        }
    }
    // Initialize game state
    const state = {
        viewport,
        facingRight: false,
        currentAnimation: "idle",
        bunnyFrameIdx: 0,
        isJumping: false,
        jumpFrameIdx: 0,
        isWalking: false,
        groundScrollX: 0,
        treeFrameIdx: 0,
        treeDirection: 1,
        bunnyWalkFramesLeft,
        bunnyWalkFramesRight,
        bunnyJumpFramesLeft,
        bunnyJumpFramesRight,
        bunnyIdleFramesLeft,
        bunnyIdleFramesRight,
        bunnyWalkToIdleFramesLeft,
        bunnyWalkToIdleFramesRight,
        treeSizes,
        treeSizeIdx: 2, // Start at largest size (180, most zoomed in)
        treeTargetSizeIdx: 2,
        treeSizeTransitionProgress: 0,
        treeCenterX: viewport.width + 60, // Center position (starts off-screen)
        currentSpeedMultiplier: 1.0, // Start at medium speed (size index 1)
    };
    // Animation timing constants (in ms)
    const WALK_INTERVAL = 120;
    const IDLE_INTERVAL = 500; // Much slower for idle
    const TREE_INTERVAL = 250;
    const JUMP_INTERVAL = 58;
    const TRANSITION_INTERVAL = 80; // Speed for walk<->idle transition
    // Scroll speed from config (characters per second)
    const SCROLL_SPEED = config.settings.scrollSpeed;
    // Walk animation timer (faster)
    const walkTimer = createAnimationTimer(WALK_INTERVAL, () => {
        if (!state.isJumping && state.currentAnimation === "walk") {
            const walkFrames = state.facingRight
                ? state.bunnyWalkFramesRight
                : state.bunnyWalkFramesLeft;
            state.bunnyFrameIdx = (state.bunnyFrameIdx + 1) % walkFrames.length;
        }
    });
    // Idle animation timer (much slower)
    const idleTimer = createAnimationTimer(IDLE_INTERVAL, () => {
        if (!state.isJumping && state.currentAnimation === "idle") {
            const frames = state.facingRight ? state.bunnyIdleFramesRight : state.bunnyIdleFramesLeft;
            state.bunnyFrameIdx = (state.bunnyFrameIdx + 1) % frames.length;
        }
    });
    // Transition animation timer (plays once, then switches to target animation)
    const transitionTimer = createAnimationTimer(TRANSITION_INTERVAL, () => {
        if (state.isJumping)
            return;
        const transitionFrames = state.facingRight
            ? state.bunnyWalkToIdleFramesRight
            : state.bunnyWalkToIdleFramesLeft;
        if (state.currentAnimation === "walk_to_idle") {
            // Playing forward: walk → idle
            state.bunnyFrameIdx++;
            if (state.bunnyFrameIdx >= transitionFrames.length) {
                // Transition complete, switch to idle
                state.currentAnimation = "idle";
                state.bunnyFrameIdx = 0;
                transitionTimer.stop();
                idleTimer.start();
            }
        }
        else if (state.currentAnimation === "idle_to_walk") {
            // Playing backward: idle → walk
            state.bunnyFrameIdx--;
            if (state.bunnyFrameIdx < 0) {
                // Transition complete, switch to walk
                state.currentAnimation = "walk";
                state.bunnyFrameIdx = 0;
                transitionTimer.stop();
                walkTimer.start();
            }
        }
    });
    // Tree animation timer (ping-pong, runs continuously)
    const treeTimer = createAnimationTimer(TREE_INTERVAL, () => {
        const currentTreeSize = state.treeSizes[state.treeSizeIdx];
        if (currentTreeSize === undefined)
            return;
        const frameCount = currentTreeSize.frames.length;
        state.treeFrameIdx += state.treeDirection;
        if (state.treeFrameIdx >= frameCount) {
            state.treeFrameIdx = frameCount - 2;
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
    // Keyboard controls - simple toggles
    document.addEventListener("keydown", (e) => {
        // Ignore auto-repeat events (when key is held down)
        if (e.repeat)
            return;
        const isLeftKey = e.key === "ArrowLeft" || e.key === "a";
        const isRightKey = e.key === "ArrowRight" || e.key === "d";
        if (isLeftKey) {
            // Toggle left walk
            if (state.isWalking && !state.facingRight && state.currentAnimation === "walk") {
                // Already walking left, stop with transition
                state.isWalking = false;
                walkTimer.stop();
                state.currentAnimation = "walk_to_idle";
                state.bunnyFrameIdx = 0;
                transitionTimer.start();
            }
            else {
                // Start walking left (or switch from right, or interrupt transition)
                const wasIdle = state.currentAnimation === "idle";
                const wasInTransition = state.currentAnimation === "walk_to_idle" || state.currentAnimation === "idle_to_walk";
                state.facingRight = false;
                state.isWalking = true;
                if (wasIdle) {
                    // Start reverse transition: idle → walk
                    idleTimer.stop();
                    const transitionFrames = state.bunnyWalkToIdleFramesLeft;
                    state.currentAnimation = "idle_to_walk";
                    state.bunnyFrameIdx = transitionFrames.length - 1; // Start from last frame
                    transitionTimer.start();
                }
                else {
                    // Switching direction or interrupting transition - go directly to walk
                    if (wasInTransition) {
                        transitionTimer.stop();
                    }
                    state.currentAnimation = "walk";
                    state.bunnyFrameIdx = 0;
                    walkTimer.start();
                }
            }
        }
        else if (isRightKey) {
            // Toggle right walk
            if (state.isWalking && state.facingRight && state.currentAnimation === "walk") {
                // Already walking right, stop with transition
                state.isWalking = false;
                walkTimer.stop();
                state.currentAnimation = "walk_to_idle";
                state.bunnyFrameIdx = 0;
                transitionTimer.start();
            }
            else {
                // Start walking right (or switch from left, or interrupt transition)
                const wasIdle = state.currentAnimation === "idle";
                const wasInTransition = state.currentAnimation === "walk_to_idle" || state.currentAnimation === "idle_to_walk";
                state.facingRight = true;
                state.isWalking = true;
                if (wasIdle) {
                    // Start reverse transition: idle → walk
                    idleTimer.stop();
                    const transitionFrames = state.bunnyWalkToIdleFramesRight;
                    state.currentAnimation = "idle_to_walk";
                    state.bunnyFrameIdx = transitionFrames.length - 1; // Start from last frame
                    transitionTimer.start();
                }
                else {
                    // Switching direction or interrupting transition - go directly to walk
                    if (wasInTransition) {
                        transitionTimer.stop();
                    }
                    state.currentAnimation = "walk";
                    state.bunnyFrameIdx = 0;
                    walkTimer.start();
                }
            }
        }
        else if (e.key === " " && !state.isJumping) {
            state.isJumping = true;
            state.jumpFrameIdx = 0;
            jumpTimer.start();
            e.preventDefault();
        }
        else if (e.key === "r") {
            state.treeCenterX = state.viewport.width + 60;
            state.groundScrollX = 0;
        }
        else if (e.key === "w" || e.key === "ArrowUp") {
            // Make tree larger (closer)
            if (state.treeTargetSizeIdx < state.treeSizes.length - 1) {
                state.treeTargetSizeIdx++;
            }
        }
        else if (e.key === "s" || e.key === "ArrowDown") {
            // Make tree smaller (farther)
            if (state.treeTargetSizeIdx > 0) {
                state.treeTargetSizeIdx--;
            }
        }
    });
    // Render loop (uses delta time for frame-rate independent movement)
    let lastTime = 0;
    const TREE_TRANSITION_DURATION_MS = 800; // Total fade transition time
    function render(currentTime) {
        // Calculate delta time in seconds
        const deltaTime = lastTime > 0 ? (currentTime - lastTime) / 1000 : 0;
        lastTime = currentTime;
        // Handle tree size transition (smooth fade with lerped speed)
        const transitionUpdate = updateSpeedTransition(state.treeSizeIdx, state.treeTargetSizeIdx, state.treeSizeTransitionProgress, deltaTime * 1000, TREE_TRANSITION_DURATION_MS);
        state.treeSizeIdx = transitionUpdate.treeSizeIdx;
        state.treeSizeTransitionProgress = transitionUpdate.treeSizeTransitionProgress;
        state.currentSpeedMultiplier = transitionUpdate.currentSpeedMultiplier;
        const isTransitioning = state.treeSizeIdx !== state.treeTargetSizeIdx;
        const { width, height } = state.viewport;
        // Create fresh buffer
        const buffer = createBuffer(width, height);
        // Draw ground (uses separate groundScrollX, stable during zoom)
        drawGround(buffer, state.groundScrollX, width, height);
        const currentTreeSize = state.treeSizes[state.treeSizeIdx];
        const currentTreeWidth = currentTreeSize?.width ?? 120;
        // Ground rows in tree ASCII: w60=3, w120=6, w180=9
        const TREE_GROUND_ROWS = [3, 6, 9];
        const SCENE_GROUND_HEIGHT = GROUND_TILE.length; // 6
        // Calculate tree Y so trunk base stays at fixed position
        // Trunk base = where tree meets ground = treeHeight - groundRows from top
        const calcTreeY = (treeHeight, sizeIdx) => {
            const groundRows = TREE_GROUND_ROWS[sizeIdx] ?? 6;
            // Trunk base should sit at bottom of viewport minus scene ground
            return height - SCENE_GROUND_HEIGHT - treeHeight + groundRows;
        };
        // Draw tree (center-anchored horizontally, trunk-anchored vertically)
        if (isTransitioning && state.treeSizeTransitionProgress > 0) {
            // Fade between current and target size
            const targetIdx = state.treeSizeIdx < state.treeTargetSizeIdx
                ? state.treeSizeIdx + 1
                : state.treeSizeIdx - 1;
            const targetTreeSize = state.treeSizes[targetIdx];
            if (currentTreeSize === undefined || targetTreeSize === undefined) {
                // Skip transition rendering if sizes unavailable
            }
            else {
                const currentFrame = currentTreeSize.frames[state.treeFrameIdx];
                const targetFrame = targetTreeSize.frames[state.treeFrameIdx % targetTreeSize.frames.length];
                if (currentFrame !== undefined && targetFrame !== undefined) {
                    const currentLines = currentFrame.split("\n");
                    const targetLines = targetFrame.split("\n");
                    const currentX = Math.floor(state.treeCenterX - currentTreeWidth / 2);
                    const targetWidth = targetTreeSize.width;
                    const targetX = Math.floor(state.treeCenterX - targetWidth / 2);
                    const currentY = calcTreeY(currentLines.length, state.treeSizeIdx);
                    const targetY = calcTreeY(targetLines.length, targetIdx);
                    drawSpriteFade(buffer, currentLines, targetLines, currentX, targetX, currentY, targetY, width, height, state.treeSizeTransitionProgress);
                }
            }
        }
        else {
            // No transition, draw normally
            const treeFrame = currentTreeSize?.frames[state.treeFrameIdx];
            if (treeFrame !== undefined) {
                const treeLines = treeFrame.split("\n");
                const treeY = calcTreeY(treeLines.length, state.treeSizeIdx);
                const treeX = Math.floor(state.treeCenterX - currentTreeWidth / 2);
                drawSprite(buffer, treeLines, treeX, treeY, width, height);
            }
        }
        // Draw bunny - select frames based on current animation and direction
        let bunnyFrames;
        let frameIdx;
        if (state.isJumping) {
            bunnyFrames = state.facingRight ? state.bunnyJumpFramesRight : state.bunnyJumpFramesLeft;
            frameIdx = state.jumpFrameIdx;
        }
        else if (state.currentAnimation === "idle") {
            bunnyFrames = state.facingRight ? state.bunnyIdleFramesRight : state.bunnyIdleFramesLeft;
            frameIdx = state.bunnyFrameIdx % bunnyFrames.length;
        }
        else if (state.currentAnimation === "walk_to_idle" || state.currentAnimation === "idle_to_walk") {
            bunnyFrames = state.facingRight ? state.bunnyWalkToIdleFramesRight : state.bunnyWalkToIdleFramesLeft;
            frameIdx = Math.max(0, Math.min(state.bunnyFrameIdx, bunnyFrames.length - 1));
        }
        else {
            bunnyFrames = state.facingRight ? state.bunnyWalkFramesRight : state.bunnyWalkFramesLeft;
            frameIdx = state.bunnyFrameIdx;
        }
        const frame = bunnyFrames[frameIdx];
        const bunnyLines = frame !== undefined ? frame.split("\n") : [];
        const bunnyX = Math.floor(width / 2) - 20;
        const bunnyY = height - bunnyLines.length - 2;
        drawSprite(buffer, bunnyLines, bunnyX, bunnyY, width, height);
        // Render to screen
        screen.textContent = renderBuffer(buffer);
        // Update scroll position using delta time (only when actually walking, not during transition)
        // Ground and tree move at the same constant speed
        const maxTreeWidth = 180;
        if (state.isWalking && state.currentAnimation === "walk") {
            const scrollAmount = SCROLL_SPEED * deltaTime;
            const scrollUpdate = calculateScrollUpdate(state.groundScrollX, state.treeCenterX, scrollAmount, state.facingRight, width, maxTreeWidth);
            state.groundScrollX = scrollUpdate.groundScrollX;
            state.treeCenterX = scrollUpdate.treeCenterX;
        }
        // Schedule next frame (requestAnimationFrame for smooth rendering)
        requestAnimationFrame(render);
    }
    // Start animation timers
    walkTimer.start();
    idleTimer.start();
    treeTimer.start();
    // Start render loop with requestAnimationFrame
    requestAnimationFrame(render);
}
// Start the application
init().catch((error) => {
    console.error("Failed to initialize:", error);
});
//# sourceMappingURL=main.js.map