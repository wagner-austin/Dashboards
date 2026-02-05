/**
 * Main entry point for the ASCII animation engine.
 * Orchestrates modules for rendering, entities, and input.
 */

import type { Config } from "./types.js";
import { measureViewport, createBuffer, renderBuffer, type ViewportState } from "./rendering/Viewport.js";
import { drawSprite, drawSpriteFade } from "./rendering/draw.js";
import { drawGround } from "./rendering/Ground.js";
import { loadSpriteFrames, loadStaticSpriteFrames, loadConfig } from "./loaders/sprites.js";
import { createInitialBunnyState, createBunnyTimers, getBunnyFrame, type BunnyFrames } from "./entities/Bunny.js";
import { createInitialTreeState, createTreeTimer, calcTreeY, getTreeFrame, getTreeTransitionFrames, type TreeSize } from "./entities/Tree.js";
import { setupKeyboardControls, type InputState } from "./input/Keyboard.js";
import { calculateScrollUpdate, updateSpeedTransition } from "./world/Parallax.js";

async function init(): Promise<void> {
  const config = await loadConfig();
  const screenEl = document.getElementById("screen");

  if (screenEl === null) {
    throw new Error("Screen element not found");
  }

  const screen: HTMLPreElement = screenEl as HTMLPreElement;
  const viewport = measureViewport(screen);

  // Load sprites
  const bunnyFrames = await loadBunnyFrames(config);
  const treeSizes = await loadTreeSizes(config);

  // Initialize state
  const bunnyState = createInitialBunnyState();
  const treeState = createInitialTreeState(viewport.width);

  const state: InputState & { viewport: ViewportState; groundScrollX: number } = {
    bunny: bunnyState,
    tree: treeState,
    viewport,
    groundScrollX: 0,
  };

  // Create timers
  const bunnyTimers = createBunnyTimers(bunnyState, bunnyFrames, {
    walk: 120,
    idle: 500,
    jump: 58,
    transition: 80,
  });
  const treeTimer = createTreeTimer(treeState, treeSizes, 250);

  // Setup input
  setupKeyboardControls(state, bunnyFrames, bunnyTimers, treeSizes);

  // Handle resize
  window.addEventListener("resize", () => {
    state.viewport = measureViewport(screen);
  });

  // Start timers
  bunnyTimers.walk.start();
  bunnyTimers.idle.start();
  treeTimer.start();

  // Render loop
  const SCROLL_SPEED = config.settings.scrollSpeed;
  const TREE_TRANSITION_DURATION_MS = 800;
  let lastTime = 0;

  function render(currentTime: number): void {
    const deltaTime = lastTime > 0 ? (currentTime - lastTime) / 1000 : 0;
    lastTime = currentTime;

    // Update tree transition
    const transitionUpdate = updateSpeedTransition(
      treeState.sizeIdx,
      treeState.targetSizeIdx,
      treeState.sizeTransitionProgress,
      deltaTime * 1000,
      TREE_TRANSITION_DURATION_MS
    );
    treeState.sizeIdx = transitionUpdate.treeSizeIdx;
    treeState.sizeTransitionProgress = transitionUpdate.treeSizeTransitionProgress;
    const isTreeTransitioning = treeState.sizeIdx !== treeState.targetSizeIdx;

    const { width, height } = state.viewport;
    const buffer = createBuffer(width, height);

    // Draw ground
    drawGround(buffer, state.groundScrollX, width, height);

    // Draw tree
    if (isTreeTransitioning && treeState.sizeTransitionProgress > 0) {
      const frames = getTreeTransitionFrames(treeState, treeSizes);
      if (frames) {
        const currentX = Math.floor(treeState.centerX - frames.current.width / 2);
        const targetX = Math.floor(treeState.centerX - frames.target.width / 2);
        const currentY = calcTreeY(frames.current.lines.length, treeState.sizeIdx, height);
        const targetY = calcTreeY(frames.target.lines.length, frames.targetIdx, height);
        drawSpriteFade(buffer, frames.current.lines, frames.target.lines, currentX, targetX, currentY, targetY, width, height, treeState.sizeTransitionProgress);
      }
    } else {
      const frame = getTreeFrame(treeState, treeSizes);
      if (frame) {
        const treeX = Math.floor(treeState.centerX - frame.width / 2);
        const treeY = calcTreeY(frame.lines.length, treeState.sizeIdx, height);
        drawSprite(buffer, frame.lines, treeX, treeY, width, height);
      }
    }

    // Draw bunny
    const bunny = getBunnyFrame(bunnyState, bunnyFrames);
    const bunnyX = Math.floor(width / 2) - 20;
    const bunnyY = height - bunny.lines.length - 2;
    drawSprite(buffer, bunny.lines, bunnyX, bunnyY, width, height);

    // Render
    screen.textContent = renderBuffer(buffer);

    // Update scroll
    if (bunnyState.isWalking && bunnyState.currentAnimation === "walk") {
      const scrollAmount = SCROLL_SPEED * deltaTime;
      const scrollUpdate = calculateScrollUpdate(
        state.groundScrollX,
        treeState.centerX,
        scrollAmount,
        bunnyState.facingRight,
        width,
        180
      );
      state.groundScrollX = scrollUpdate.groundScrollX;
      treeState.centerX = scrollUpdate.treeCenterX;
    }

    requestAnimationFrame(render);
  }

  requestAnimationFrame(render);
}

async function loadBunnyFrames(_config: Config): Promise<BunnyFrames> {
  const [walkLeft, walkRight, jumpLeft, jumpRight, idleLeft, idleRight, walkToIdleLeft, walkToIdleRight] = await Promise.all([
    loadSpriteFrames("bunny", "walk", 50, "left"),
    loadSpriteFrames("bunny", "walk", 50, "right"),
    loadSpriteFrames("bunny", "jump", 50, "left"),
    loadSpriteFrames("bunny", "jump", 50, "right"),
    loadSpriteFrames("bunny", "idle", 40, "left"),
    loadSpriteFrames("bunny", "idle", 40, "right"),
    loadSpriteFrames("bunny", "walk_to_idle", 40, "left"),
    loadSpriteFrames("bunny", "walk_to_idle", 40, "right"),
  ]);

  return {
    walkLeft: walkLeft.frames,
    walkRight: walkRight.frames,
    jumpLeft: jumpLeft.frames,
    jumpRight: jumpRight.frames,
    idleLeft: idleLeft.frames,
    idleRight: idleRight.frames,
    walkToIdleLeft: walkToIdleLeft.frames,
    walkToIdleRight: walkToIdleRight.frames,
  };
}

async function loadTreeSizes(_config: Config): Promise<TreeSize[]> {
  const widths = [60, 120, 180];
  const sizes: TreeSize[] = [];
  for (const w of widths) {
    const set = await loadStaticSpriteFrames("tree", w);
    sizes.push({ width: w, frames: set.frames });
  }
  return sizes;
}

init().catch((error: unknown) => {
  console.error("Failed to initialize:", error);
});
