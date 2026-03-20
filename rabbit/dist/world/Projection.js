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
/** Default wrap iterations for Z-wrapping coverage. */
export const DEFAULT_WRAP_ITERATIONS = 2;
/**
 * Create default projection configuration.
 *
 * Returns:
 *     ProjectionConfig: Configuration with balanced perspective settings.
 */
export function createProjectionConfig() {
    return {
        focalLength: 50,
        horizonY: 0.12,
        nearZ: 40,
        farZ: 200,
        groundY: 0.85,
        parallaxStrength: 0.5,
        wrapIterations: DEFAULT_WRAP_ITERATIONS,
    };
}
/** Default camera Z position (distance from origin). */
export const DEFAULT_CAMERA_Z = 55;
/** World width for entity wrapping (must be large enough for sprites to fully exit screen). */
export const WORLD_WIDTH = 800;
/**
 * Calculate camera depth bounds from projection configuration.
 *
 * Uses visibleDepth (farZ - nearZ) as the wrap range to match tree Z-wrapping
 * interval, ensuring seamless infinite depth scrolling with no empty gaps.
 *
 * Args:
 *     minTreeWorldZ: WorldZ of closest trees (used for starting position).
 *     maxTreeWorldZ: WorldZ of farthest trees (unused, kept for compatibility).
 *     projectionConfig: Projection configuration with nearZ/farZ.
 *
 * Returns:
 *     DepthBounds: Computed depth bounds for camera movement.
 */
export function calculateDepthBounds(minTreeWorldZ, _maxTreeWorldZ, projectionConfig) {
    const visibleDepth = projectionConfig.farZ - projectionConfig.nearZ;
    const minZ = minTreeWorldZ - projectionConfig.farZ;
    const maxZ = minZ + visibleDepth;
    return {
        minZ,
        maxZ,
        range: visibleDepth,
    };
}
/**
 * Create initial camera state.
 *
 * Returns:
 *     Camera: Camera positioned at origin with default depth.
 */
export function createCamera() {
    return { x: 0, z: DEFAULT_CAMERA_Z };
}
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
export function project(worldX, worldZ, camera, viewportWidth, viewportHeight, config) {
    const relativeZ = worldZ - camera.z;
    // Use nearZ as minimum visible distance (near clip plane)
    if (relativeZ < config.nearZ || relativeZ > config.farZ) {
        return { x: 0, y: 0, scale: 0, visible: false };
    }
    const relativeX = worldX - camera.x;
    const centerX = viewportWidth / 2;
    const horizonY = viewportHeight * config.horizonY;
    const groundY = viewportHeight * config.groundY;
    // Scale for sprite sizing - uses focalLength
    const scale = config.focalLength / relativeZ;
    // X position - linear parallax based on depth ratio
    // Close objects (small relativeZ) have higher parallax factor
    // Far objects (large relativeZ) have lower parallax factor
    const depthRange = config.farZ - config.nearZ;
    const normalizedDepth = (relativeZ - config.nearZ) / depthRange;
    const xParallax = (1 - normalizedDepth) * config.parallaxStrength;
    const screenX = centerX + relativeX * xParallax;
    // Y position - uses inverse depth with fixed base (independent of focalLength)
    // Close objects move down past ground, far objects rise toward horizon
    const Y_BASE = 50;
    const yScale = Y_BASE / relativeZ;
    const yRange = groundY - horizonY;
    const screenY = horizonY + yRange * yScale;
    return {
        x: Math.round(screenX),
        y: Math.round(screenY),
        scale: Math.min(Math.max(scale, 0), 1.5),
        visible: true,
    };
}
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
export function scaleToSizeIndex(scale, sizeCount) {
    if (sizeCount <= 1) {
        return 0;
    }
    const normalized = Math.min(Math.max(scale, 0), 1);
    return Math.round(normalized * (sizeCount - 1));
}
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
export function wrapPosition(entityX, cameraX, worldWidth) {
    const relativeX = entityX - cameraX;
    const halfWorld = worldWidth / 2;
    if (relativeX < -halfWorld) {
        return entityX + worldWidth;
    }
    else if (relativeX > halfWorld) {
        return entityX - worldWidth;
    }
    return entityX;
}
/**
 * Wrap camera depth position for infinite depth scrolling.
 *
 * Uses modular arithmetic to wrap positions into [minZ, maxZ) range.
 * Equivalent positions at exact multiples of range map to minZ.
 *
 * Args:
 *     cameraZ: Camera depth position.
 *     minZ: Minimum depth bound (inclusive).
 *     maxZ: Maximum depth bound (exclusive for wrapping).
 *
 * Returns:
 *     number: Wrapped camera Z position within [minZ, maxZ).
 */
export function wrapDepth(cameraZ, minZ, maxZ) {
    if (cameraZ >= minZ && cameraZ < maxZ) {
        return cameraZ;
    }
    const range = maxZ - minZ;
    const normalized = cameraZ - minZ;
    const wrapped = ((normalized % range) + range) % range;
    return minZ + wrapped;
}
/** Test hooks for internal functions. */
export const _test_hooks = {
    createProjectionConfig,
    createCamera,
    project,
    scaleToSizeIndex,
    wrapPosition,
    wrapDepth,
    calculateDepthBounds,
    DEFAULT_WRAP_ITERATIONS,
};
//# sourceMappingURL=Projection.js.map