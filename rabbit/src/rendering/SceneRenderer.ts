/**
 * Scene renderer - handles frame-by-frame rendering of the entire scene.
 * Coordinates layers, entities, ground, and scroll updates.
 */

import { createBuffer, renderBuffer, type ViewportState } from "./Viewport.js";
import { drawSprite, drawSpriteFade } from "./draw.js";
import { drawGround } from "./Ground.js";
import { getBunnyFrame, type BunnyFrames, type BunnyState } from "../entities/Bunny.js";
import { calcTreeY, getTreeFrame, getTreeTransitionFrames, type TreeSize, type TreeState } from "../entities/Tree.js";
import { calculateScrollUpdate, updateSpeedTransition } from "../world/Parallax.js";
import { renderAllLayers, renderForegroundLayers, type SceneState } from "../layers/index.js";

/** Render state for a single frame */
export interface RenderState {
  bunnyState: BunnyState;
  treeState: TreeState;
  sceneState: SceneState;
  viewport: ViewportState;
  groundScrollX: number;
  lastTime: number;
}

/** Render a single frame - pure function for testability */
export function renderFrame(
  state: RenderState,
  bunnyFrames: BunnyFrames,
  treeSizes: TreeSize[],
  screen: HTMLPreElement,
  currentTime: number,
  scrollSpeed: number,
  transitionDurationMs: number
): { groundScrollX: number; lastTime: number } {
  const deltaTime = state.lastTime > 0 ? (currentTime - state.lastTime) / 1000 : 0;

  // Update tree transition
  const transitionUpdate = updateSpeedTransition(
    state.treeState.sizeIdx,
    state.treeState.targetSizeIdx,
    state.treeState.sizeTransitionProgress,
    deltaTime * 1000,
    transitionDurationMs
  );
  state.treeState.sizeIdx = transitionUpdate.treeSizeIdx;
  state.treeState.sizeTransitionProgress = transitionUpdate.treeSizeTransitionProgress;
  const isTreeTransitioning = state.treeState.sizeIdx !== state.treeState.targetSizeIdx;

  const { width, height } = state.viewport;
  const buffer = createBuffer(width, height);

  // Render background layers (behind ground)
  renderAllLayers(buffer, state.sceneState, width, height);

  // Draw ground
  drawGround(buffer, state.groundScrollX, width, height);

  // Draw tree (special entity - rendered on top of layers)
  if (isTreeTransitioning && state.treeState.sizeTransitionProgress > 0) {
    const frames = getTreeTransitionFrames(state.treeState, treeSizes);
    if (frames !== null) {
      const currentX = Math.floor(state.treeState.centerX - frames.current.width / 2);
      const targetX = Math.floor(state.treeState.centerX - frames.target.width / 2);
      const currentY = calcTreeY(frames.current.lines.length, state.treeState.sizeIdx, height);
      const targetY = calcTreeY(frames.target.lines.length, frames.targetIdx, height);
      drawSpriteFade(buffer, frames.current.lines, frames.target.lines, currentX, targetX, currentY, targetY, width, height, state.treeState.sizeTransitionProgress);
    }
  } else {
    const frame = getTreeFrame(state.treeState, treeSizes);
    if (frame !== null) {
      const treeX = Math.floor(state.treeState.centerX - frame.width / 2);
      const treeY = calcTreeY(frame.lines.length, state.treeState.sizeIdx, height);
      drawSprite(buffer, frame.lines, treeX, treeY, width, height);
    }
  }

  // Draw bunny
  const bunny = getBunnyFrame(state.bunnyState, bunnyFrames);
  const bunnyX = Math.floor(width / 2) - 20;
  const bunnyY = height - bunny.lines.length - 2;
  drawSprite(buffer, bunny.lines, bunnyX, bunnyY, width, height);

  // Render foreground layers (in front of bunny)
  renderForegroundLayers(buffer, state.sceneState, width, height);

  // Render
  screen.textContent = renderBuffer(buffer);

  // Update scroll
  let newGroundScrollX = state.groundScrollX;
  if (state.bunnyState.isWalking && state.bunnyState.currentAnimation === "walk") {
    const scrollAmount = scrollSpeed * deltaTime;
    const scrollUpdate = calculateScrollUpdate(
      state.groundScrollX,
      state.treeState.centerX,
      scrollAmount,
      state.bunnyState.facingRight,
      width,
      180
    );
    newGroundScrollX = scrollUpdate.groundScrollX;
    state.treeState.centerX = scrollUpdate.treeCenterX;

    // Update camera for layer parallax
    const cameraDirection = state.bunnyState.facingRight ? 1 : -1;
    state.sceneState.cameraX += scrollAmount * cameraDirection;
  }

  return { groundScrollX: newGroundScrollX, lastTime: currentTime };
}
