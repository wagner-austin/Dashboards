/**
 * Layer system types.
 */
/**
 * Create initial scene state.
 *
 * Args:
 *     layers: Layer instances to include.
 *     camera: Initial camera position.
 *
 * Returns:
 *     SceneState with provided layers and camera.
 */
export function createSceneState(layers, camera) {
    return {
        layers,
        camera,
    };
}
//# sourceMappingURL=types.js.map