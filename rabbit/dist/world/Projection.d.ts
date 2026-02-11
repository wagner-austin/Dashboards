/**
 * 3D projection system for unified depth handling.
 *
 * Provides perspective projection with decoupled controls for:
 * - Scale: Size based on depth (further = smaller), controlled by focalLength
 * - Y position: Vertical position based on depth ratio, independent of focalLength
 * - X parallax: Horizontal offset controlled by parallaxStrength
 *
 * All world positions use (x, z) where z is depth into the scene.
 */
/**
 * Camera position in world space.
 *
 * x: Horizontal position (affected by left/right movement).
 * z: Depth position (affected by forward/backward movement).
 */
export interface Camera {
    readonly x: number;
    readonly z: number;
}
/**
 * Configuration for perspective projection.
 *
 * focalLength: Controls scale/size of objects (higher = larger at same depth).
 * horizonY: Vertical position of horizon as fraction from top (0-1).
 * nearZ: Minimum visible depth (objects closer are not rendered).
 * farZ: Maximum visible depth (horizon distance).
 * groundY: Vertical position of ground plane as fraction from top (0-1).
 * parallaxStrength: Multiplier for horizontal parallax effect (0=none, 1=full).
 */
export interface ProjectionConfig {
    readonly focalLength: number;
    readonly horizonY: number;
    readonly nearZ: number;
    readonly farZ: number;
    readonly groundY: number;
    readonly parallaxStrength: number;
}
/**
 * Result of projecting a world position to screen coordinates.
 *
 * x: Screen X coordinate (pixels/characters).
 * y: Screen Y coordinate (pixels/characters).
 * scale: Size multiplier (0-1.5, where 1 is normal size).
 * visible: Whether the position is within visible range.
 */
export interface ScreenPosition {
    readonly x: number;
    readonly y: number;
    readonly scale: number;
    readonly visible: boolean;
}
/**
 * Create default projection configuration.
 *
 * Returns:
 *     ProjectionConfig: Configuration with balanced perspective settings.
 */
export declare function createProjectionConfig(): ProjectionConfig;
/** Default camera Z position (distance from origin). */
export declare const DEFAULT_CAMERA_Z = 55;
/** World width for entity wrapping (must be large enough for sprites to fully exit screen). */
export declare const WORLD_WIDTH = 800;
/**
 * Create initial camera state.
 *
 * Returns:
 *     Camera: Camera positioned at origin with default depth.
 */
export declare function createCamera(): Camera;
/**
 * Project a world position to screen coordinates.
 *
 * Uses perspective projection with decoupled controls:
 * - Scale is calculated from focalLength/depth for sprite sizing
 * - Y position uses depth ratio directly, independent of focalLength
 * - X position uses scale multiplied by parallaxStrength
 *
 * Args:
 *     worldX: World X coordinate.
 *     worldZ: World Z coordinate (depth).
 *     camera: Current camera position.
 *     viewportWidth: Screen width in characters.
 *     viewportHeight: Screen height in characters.
 *     config: Projection configuration.
 *
 * Returns:
 *     ScreenPosition: Projected coordinates with x, y, scale, and visibility.
 */
export declare function project(worldX: number, worldZ: number, camera: Camera, viewportWidth: number, viewportHeight: number, config: ProjectionConfig): ScreenPosition;
/**
 * Map projection scale to sprite size index.
 *
 * Converts continuous scale value to discrete size index for sprite selection.
 *
 * Args:
 *     scale: Projection scale (0-1.5).
 *     sizeCount: Number of available sprite sizes.
 *
 * Returns:
 *     number: Index into sizes array (0=smallest, sizeCount-1=largest).
 */
export declare function scaleToSizeIndex(scale: number, sizeCount: number): number;
/**
 * Wrap entity position to keep it within world bounds relative to camera.
 *
 * When entity is too far behind camera, wraps it ahead.
 * When entity is too far ahead, wraps it behind.
 *
 * Args:
 *     entityX: Entity world X position.
 *     cameraX: Camera world X position.
 *     worldWidth: Total world width for wrapping.
 *
 * Returns:
 *     number: Wrapped entity X position.
 */
export declare function wrapPosition(entityX: number, cameraX: number, worldWidth: number): number;
/** Test hooks for internal functions. */
export declare const _test_hooks: {
    createProjectionConfig: typeof createProjectionConfig;
    createCamera: typeof createCamera;
    project: typeof project;
    scaleToSizeIndex: typeof scaleToSizeIndex;
    wrapPosition: typeof wrapPosition;
};
//# sourceMappingURL=Projection.d.ts.map