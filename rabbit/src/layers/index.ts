/**
 * Layer system exports.
 */

export {
  type ValidatedLayer,
  type SceneSpriteState,
  type LayerInstance,
  type SceneState,
  createSceneState,
} from "./types.js";

export {
  validateLayersConfig,
} from "./validation.js";

export {
  getParallaxX,
  renderLayer,
  renderAllLayers,
  renderForegroundLayers,
} from "./renderer.js";
