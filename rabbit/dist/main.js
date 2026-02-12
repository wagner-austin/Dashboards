/**
 * Main entry point for the ASCII animation engine.
 *
 * Orchestrates modules for rendering, entities, and input.
 * Uses progressive loading to populate scene as sprites load.
 */
import { measureViewport } from "./rendering/Viewport.js";
import { renderFrame } from "./rendering/SceneRenderer.js";
import { createAnimationTimer } from "./loaders/sprites.js";
import { createInitialBunnyState, createBunnyTimers } from "./entities/Bunny.js";
import { setupKeyboardControls, processDepthMovement, processHorizontalMovement } from "./input/Keyboard.js";
import { setupTouchControls } from "./input/Touch.js";
import { processLayersConfig, createSceneState } from "./layers/index.js";
import { createProgressiveLayerInstances } from "./loaders/layers.js";
import { createLayerAnimationCallback } from "./entities/SceneSprite.js";
import { createCamera, createProjectionConfig, calculateDepthBounds } from "./world/Projection.js";
import { layerToWorldZ } from "./layers/widths.js";
import { createMutableSpriteRegistry } from "./loaders/progressive.js";
import { initializeAudio, setupTrackSwitcher, } from "./audio/index.js";
import { loadConfig, runProgressiveLoad, createDefaultAudioDependencies, } from "./io/index.js";
/**
 * Create default dependencies using real implementations.
 *
 * Returns:
 *     MainDependencies with browser implementations.
 */
function createDefaultDependencies() {
    return {
        getScreenElement: () => document.getElementById("screen"),
        loadConfigFn: loadConfig,
        runProgressiveLoadFn: runProgressiveLoad,
        requestAnimationFrameFn: (callback) => requestAnimationFrame(callback),
        audioDeps: createDefaultAudioDependencies(),
    };
}
/**
 * Collect all sprite names referenced in config.
 *
 * Gathers sprite names from both manual layers and autoLayers config.
 *
 * Args:
 *     config: Application config.
 *
 * Returns:
 *     Array of unique sprite names.
 */
function collectAllSpriteNames(config) {
    const names = new Set();
    // From manual layers
    for (const layer of config.layers) {
        if (layer.sprites !== undefined) {
            for (const name of layer.sprites) {
                names.add(name);
            }
        }
    }
    // From autoLayers
    if (config.autoLayers !== undefined) {
        for (const name of config.autoLayers.sprites) {
            names.add(name);
        }
    }
    return [...names];
}
/**
 * Initialize the application with progressive loading.
 *
 * Starts render loop immediately with ground visible, then progressively
 * loads grass, bunny, and trees (smallest to largest). Scene populates
 * as sprites load.
 *
 * Args:
 *     deps: Dependencies for testing or production.
 *
 * Raises:
 *     Error: If screen element not found or autoLayers not configured.
 */
export async function init(deps = createDefaultDependencies()) {
    const config = await deps.loadConfigFn();
    const screenEl = deps.getScreenElement();
    if (screenEl === null) {
        throw new Error("Screen element not found");
    }
    const screen = screenEl;
    const viewport = measureViewport(screen);
    // Require autoLayers config for depth bounds
    if (config.autoLayers === undefined) {
        throw new Error("config.autoLayers is required for depth movement");
    }
    // Create mutable sprite registry with all sprite names
    const spriteNames = collectAllSpriteNames(config);
    const spriteRegistry = createMutableSpriteRegistry(spriteNames);
    // Process layers (including auto-generated layers if configured)
    const validatedLayers = processLayersConfig(config.layers, config.autoLayers);
    // Create layer instances with mutable registry (entities start with empty sizes)
    const layerInstances = createProgressiveLayerInstances(validatedLayers, spriteRegistry, viewport.width);
    // Create camera and projection config
    const camera = createCamera();
    const projectionConfig = createProjectionConfig();
    // Calculate depth bounds from autoLayers config
    const minTreeWorldZ = layerToWorldZ(config.autoLayers.minLayer);
    const maxTreeWorldZ = layerToWorldZ(config.autoLayers.maxLayer);
    const depthBounds = calculateDepthBounds(minTreeWorldZ, maxTreeWorldZ, projectionConfig);
    // Create scene state with camera and depth bounds
    const sceneState = createSceneState(layerInstances, camera, depthBounds);
    // Initialize entity state (bunny state starts with no frames)
    const bunnyState = createInitialBunnyState();
    // Mutable reference for bunny frames (set when bunny loading completes)
    let bunnyFrames = null;
    const state = {
        bunny: bunnyState,
        viewport,
        camera,
        depthBounds,
        horizontalHeld: null,
        verticalHeld: null,
        scene: sceneState,
    };
    // Handle resize
    window.addEventListener("resize", () => {
        state.viewport = measureViewport(screen);
    });
    // Initialize audio
    const audioSystem = initializeAudio(config.audio, deps.audioDeps);
    if (audioSystem !== null) {
        setupTrackSwitcher(audioSystem, (type, handler) => {
            document.addEventListener(type, handler);
        });
    }
    // Layer animation timer
    const layerAnimationCallback = createLayerAnimationCallback(sceneState);
    const layerAnimationTimer = createAnimationTimer(400, layerAnimationCallback);
    layerAnimationTimer.start();
    // Render loop - starts immediately (ground visible, sprites appear as they load)
    const SCROLL_SPEED = config.settings.scrollSpeed;
    let lastTime = 0;
    function render(currentTime) {
        // Calculate delta time for frame-rate independent movement
        const deltaTime = lastTime > 0 ? (currentTime - lastTime) / 1000 : 0;
        // Process movement input only if bunny is loaded
        if (bunnyFrames !== null) {
            processDepthMovement(state, deltaTime);
            processHorizontalMovement(state, deltaTime);
        }
        // Sync camera from input state to scene state
        state.scene.camera = state.camera;
        const renderState = {
            bunnyState,
            sceneState: state.scene,
            viewport: state.viewport,
            lastTime,
            projectionConfig,
        };
        // Only render bunny if frames are loaded
        if (bunnyFrames !== null) {
            const result = renderFrame(renderState, bunnyFrames, screen, currentTime, SCROLL_SPEED);
            lastTime = result.lastTime;
        }
        else {
            // Render without bunny (just layers and ground)
            const result = renderFrame(renderState, createEmptyBunnyFrames(), screen, currentTime, SCROLL_SPEED);
            lastTime = result.lastTime;
        }
        // Sync camera back from scene state to input state
        state.camera = state.scene.camera;
        deps.requestAnimationFrameFn(render);
    }
    // Start render loop immediately
    deps.requestAnimationFrameFn(render);
    // Run progressive loading in parallel (sprites appear as they load)
    await deps.runProgressiveLoadFn(config, spriteRegistry, (_progress) => {
        // Progress callback - could update a loading indicator here
        // Sprites are automatically visible as they're added to registry
    }, (loadedBunnyFrames) => {
        // Bunny loaded callback - set up controls immediately
        bunnyFrames = loadedBunnyFrames;
        // Create callback to check horizontal input for animation completion
        const isHorizontalHeld = () => state.horizontalHeld !== null;
        // Create timers now that bunny is loaded
        const bunnyTimers = createBunnyTimers(bunnyState, bunnyFrames, {
            walk: 120,
            idle: 500,
            jump: 58,
            transition: 50,
            hop: 150,
        }, isHorizontalHeld);
        // Setup input controls
        setupKeyboardControls(state, bunnyFrames, bunnyTimers);
        setupTouchControls(state, bunnyFrames, bunnyTimers);
        // Start bunny animation timers
        bunnyTimers.walk.start();
        bunnyTimers.idle.start();
    });
}
/**
 * Create empty bunny frames for rendering before bunny is loaded.
 *
 * Returns:
 *     BunnyFrames with empty arrays for all animations.
 */
function createEmptyBunnyFrames() {
    const empty = [];
    return {
        walkLeft: empty,
        walkRight: empty,
        jumpLeft: empty,
        jumpRight: empty,
        idleLeft: empty,
        idleRight: empty,
        walkToIdleLeft: empty,
        walkToIdleRight: empty,
        walkToTurnAwayLeft: empty,
        walkToTurnAwayRight: empty,
        walkToTurnTowardLeft: empty,
        walkToTurnTowardRight: empty,
        hopAway: empty,
        hopToward: empty,
    };
}
/**
 * Check if running in test environment.
 *
 * Returns:
 *     True if MODE is 'test'.
 */
function isTestEnvironment() {
    const meta = import.meta;
    return meta.env?.MODE === "test";
}
/** Test hooks for internal functions */
export const _test_hooks = {
    createDefaultDependencies,
    isTestEnvironment,
    collectAllSpriteNames,
    createEmptyBunnyFrames,
};
//# sourceMappingURL=main.js.map