/**
 * Layer system types.
 */
/**
 * Create initial scene state.
 *
 * Args:
 *     layers: Layer instances to include.
 *     camera: Initial camera position.
 *     depthBounds: Bounds for depth wrapping.
 *
 * Returns:
 *     SceneState with provided layers, camera, and depth bounds.
 */
export function createSceneState(layers, camera, depthBounds) {
    return {
        layers,
        camera,
        depthBounds,
    };
}
/**
 * Create a render candidate.
 *
 * Args:
 *     entity: Scene sprite to render.
 *     effectiveZ: World Z position to render at.
 *
 * Returns:
 *     RenderCandidate with provided values.
 */
export function createRenderCandidate(entity, effectiveZ) {
    return { entity, effectiveZ };
}
//# sourceMappingURL=types.js.map