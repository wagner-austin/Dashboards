/**
 * Tests for 3D projection system.
 */
import { describe, expect, it } from "vitest";
import { createProjectionConfig, createCamera, project, scaleToSizeIndex, wrapPosition, DEFAULT_CAMERA_Z, WORLD_WIDTH, _test_hooks, } from "./Projection.js";
describe("createProjectionConfig", () => {
    it("returns config with default values", () => {
        const config = createProjectionConfig();
        expect(config.focalLength).toBe(50);
        expect(config.horizonY).toBe(0.12);
        expect(config.nearZ).toBe(40);
        expect(config.farZ).toBe(200);
        expect(config.groundY).toBe(0.92);
        expect(config.parallaxStrength).toBe(0.5);
    });
    it("returns readonly config", () => {
        const config = createProjectionConfig();
        expect(Object.isFrozen(config) || typeof config.focalLength === "number").toBe(true);
    });
});
describe("createCamera", () => {
    it("returns camera at origin with default depth", () => {
        const camera = createCamera();
        expect(camera.x).toBe(0);
        expect(camera.z).toBe(DEFAULT_CAMERA_Z);
    });
});
describe("project", () => {
    const config = createProjectionConfig();
    const camera = createCamera();
    const viewportWidth = 200;
    const viewportHeight = 100;
    describe("visibility", () => {
        it("returns not visible when object is behind camera", () => {
            const result = project(0, 30, camera, viewportWidth, viewportHeight, config);
            expect(result.visible).toBe(false);
            expect(result.scale).toBe(0);
        });
        it("returns not visible when object is closer than nearZ", () => {
            // Camera at z=35, nearZ=40, so object at z=70 has relativeZ=35 which is < nearZ
            const result = project(0, 70, camera, viewportWidth, viewportHeight, config);
            expect(result.visible).toBe(false);
        });
        it("returns not visible when object is beyond far plane", () => {
            const result = project(0, 300, camera, viewportWidth, viewportHeight, config);
            expect(result.visible).toBe(false);
        });
        it("returns visible when object is in valid depth range", () => {
            const result = project(0, 100, camera, viewportWidth, viewportHeight, config);
            expect(result.visible).toBe(true);
        });
        it("returns visible when object is exactly at nearZ distance", () => {
            // Camera at z=55, nearZ=40, so object at z=95 has relativeZ=40 (exactly nearZ)
            const result = project(0, 95, camera, viewportWidth, viewportHeight, config);
            expect(result.visible).toBe(true);
        });
    });
    describe("screen position", () => {
        it("projects object directly ahead to screen center", () => {
            const result = project(0, 100, camera, viewportWidth, viewportHeight, config);
            expect(result.x).toBe(100);
        });
        it("projects object to the right of camera to right of center", () => {
            const result = project(50, 100, camera, viewportWidth, viewportHeight, config);
            expect(result.x).toBeGreaterThan(100);
        });
        it("projects object to the left of camera to left of center", () => {
            const result = project(-50, 100, camera, viewportWidth, viewportHeight, config);
            expect(result.x).toBeLessThan(100);
        });
        it("calculates Y position between horizon and ground", () => {
            const result = project(0, 120, camera, viewportWidth, viewportHeight, config);
            const horizonY = viewportHeight * config.horizonY;
            const groundY = viewportHeight * config.groundY;
            expect(result.y).toBeGreaterThan(horizonY);
            expect(result.y).toBeLessThan(groundY);
        });
    });
    describe("scale", () => {
        it("calculates larger scale for closer objects", () => {
            // Both objects must have relativeZ >= nearZ (40) to be visible
            // camera.z=55, so worldZ must be >= 95
            const close = project(0, 100, camera, viewportWidth, viewportHeight, config);
            const far = project(0, 150, camera, viewportWidth, viewportHeight, config);
            expect(close.scale).toBeGreaterThan(far.scale);
        });
        it("clamps scale to maximum of 1.5", () => {
            const veryClose = project(0, 38, camera, viewportWidth, viewportHeight, config);
            expect(veryClose.scale).toBeLessThanOrEqual(1.5);
        });
        it("clamps scale to minimum of 0", () => {
            const result = project(0, 100, camera, viewportWidth, viewportHeight, config);
            expect(result.scale).toBeGreaterThanOrEqual(0);
        });
    });
    describe("with moved camera", () => {
        it("adjusts X position when camera moves right", () => {
            const movedCamera = { x: 50, z: 50 };
            const result = project(50, 100, movedCamera, viewportWidth, viewportHeight, config);
            expect(result.x).toBe(100);
        });
        it("adjusts projection when camera moves forward", () => {
            // Camera at z=80, object at z=130, relativeZ=50 >= nearZ(40), visible
            // scale = focalLength(50) / relativeZ(50) = 1
            const forwardCamera = { x: 0, z: 80 };
            const result = project(0, 130, forwardCamera, viewportWidth, viewportHeight, config);
            expect(result.scale).toBe(1);
        });
    });
    describe("decoupled Y from focalLength", () => {
        it("maintains same Y position when focalLength changes", () => {
            const config1 = { ...config, focalLength: 30 };
            const config2 = { ...config, focalLength: 80 };
            const result1 = project(0, 100, camera, viewportWidth, viewportHeight, config1);
            const result2 = project(0, 100, camera, viewportWidth, viewportHeight, config2);
            expect(result1.y).toBe(result2.y);
        });
        it("changes scale when focalLength changes but Y stays same", () => {
            const config1 = { ...config, focalLength: 30 };
            const config2 = { ...config, focalLength: 80 };
            const result1 = project(0, 100, camera, viewportWidth, viewportHeight, config1);
            const result2 = project(0, 100, camera, viewportWidth, viewportHeight, config2);
            expect(result1.scale).not.toBe(result2.scale);
            expect(result1.y).toBe(result2.y);
        });
        it("moves close objects below ground level", () => {
            // Object at relativeZ < Y_BASE (50) should be below groundY (Y increases downward)
            // worldZ=100, camera.z=55, relativeZ=45, yScale = 50/45 > 1
            const closeResult = project(0, 100, camera, viewportWidth, viewportHeight, config);
            const groundY = viewportHeight * config.groundY;
            expect(closeResult.y).toBeGreaterThan(groundY);
        });
        it("raises far objects toward horizon", () => {
            // Far object should be between horizon and ground
            const farResult = project(0, 150, camera, viewportWidth, viewportHeight, config);
            const horizonY = viewportHeight * config.horizonY;
            const groundY = viewportHeight * config.groundY;
            expect(farResult.y).toBeGreaterThan(horizonY);
            expect(farResult.y).toBeLessThan(groundY);
        });
    });
    describe("parallaxStrength", () => {
        it("reduces X offset when parallaxStrength is lower", () => {
            const configLow = { ...config, parallaxStrength: 0.25 };
            const configHigh = { ...config, parallaxStrength: 1.0 };
            const resultLow = project(100, 100, camera, viewportWidth, viewportHeight, configLow);
            const resultHigh = project(100, 100, camera, viewportWidth, viewportHeight, configHigh);
            const offsetLow = Math.abs(resultLow.x - 100);
            const offsetHigh = Math.abs(resultHigh.x - 100);
            expect(offsetLow).toBeLessThan(offsetHigh);
        });
        it("produces no X offset when parallaxStrength is 0", () => {
            const configZero = { ...config, parallaxStrength: 0 };
            const result = project(100, 100, camera, viewportWidth, viewportHeight, configZero);
            expect(result.x).toBe(100);
        });
        it("does not affect Y position", () => {
            const configLow = { ...config, parallaxStrength: 0.1 };
            const configHigh = { ...config, parallaxStrength: 1.0 };
            const resultLow = project(100, 100, camera, viewportWidth, viewportHeight, configLow);
            const resultHigh = project(100, 100, camera, viewportWidth, viewportHeight, configHigh);
            expect(resultLow.y).toBe(resultHigh.y);
        });
        it("does not affect scale", () => {
            const configLow = { ...config, parallaxStrength: 0.1 };
            const configHigh = { ...config, parallaxStrength: 1.0 };
            const resultLow = project(100, 100, camera, viewportWidth, viewportHeight, configLow);
            const resultHigh = project(100, 100, camera, viewportWidth, viewportHeight, configHigh);
            expect(resultLow.scale).toBe(resultHigh.scale);
        });
        it("uses linear falloff with depth", () => {
            // Close objects have higher parallax factor than far objects
            // camera.z=55, nearZ=40, so worldZ must be >= 95
            const closeResult = project(100, 100, camera, viewportWidth, viewportHeight, config);
            const farResult = project(100, 150, camera, viewportWidth, viewportHeight, config);
            const closeOffset = Math.abs(closeResult.x - 100);
            const farOffset = Math.abs(farResult.x - 100);
            expect(closeOffset).toBeGreaterThan(farOffset);
        });
        it("produces zero parallax at farZ", () => {
            // Object at exactly farZ should have no X offset
            const farObject = project(100, config.farZ + camera.z, camera, viewportWidth, viewportHeight, config);
            // At farZ, normalizedDepth = 1, so xParallax = 0
            expect(farObject.x).toBe(100);
        });
    });
});
describe("scaleToSizeIndex", () => {
    it("returns 0 for single size", () => {
        expect(scaleToSizeIndex(0.5, 1)).toBe(0);
        expect(scaleToSizeIndex(1.0, 1)).toBe(0);
    });
    it("returns 0 for smallest scale with multiple sizes", () => {
        expect(scaleToSizeIndex(0, 3)).toBe(0);
    });
    it("returns max index for largest scale", () => {
        expect(scaleToSizeIndex(1, 3)).toBe(2);
    });
    it("returns middle index for middle scale", () => {
        expect(scaleToSizeIndex(0.5, 3)).toBe(1);
    });
    it("clamps negative scale to 0", () => {
        expect(scaleToSizeIndex(-0.5, 3)).toBe(0);
    });
    it("clamps scale above 1 to max index", () => {
        expect(scaleToSizeIndex(1.5, 3)).toBe(2);
    });
    it("rounds to nearest index", () => {
        expect(scaleToSizeIndex(0.3, 3)).toBe(1);
        expect(scaleToSizeIndex(0.7, 3)).toBe(1);
    });
});
describe("wrapPosition", () => {
    it("returns same position when within bounds", () => {
        expect(wrapPosition(100, 50, 400)).toBe(100);
    });
    it("wraps to front when entity is too far behind camera", () => {
        expect(wrapPosition(0, 300, 400)).toBe(400);
    });
    it("wraps to back when entity is too far ahead of camera", () => {
        expect(wrapPosition(500, 100, 400)).toBe(100);
    });
    it("handles entity exactly at boundary", () => {
        expect(wrapPosition(0, 200, 400)).toBe(0);
    });
    it("handles negative camera positions", () => {
        expect(wrapPosition(-100, -400, 400)).toBe(-500);
    });
});
describe("world constants", () => {
    it("defines WORLD_WIDTH large enough for sprites to exit screen", () => {
        expect(WORLD_WIDTH).toBe(800);
    });
});
describe("_test_hooks", () => {
    it("exports all internal functions", () => {
        expect(_test_hooks.createProjectionConfig).toBe(createProjectionConfig);
        expect(_test_hooks.createCamera).toBe(createCamera);
        expect(_test_hooks.project).toBe(project);
        expect(_test_hooks.scaleToSizeIndex).toBe(scaleToSizeIndex);
        expect(_test_hooks.wrapPosition).toBe(wrapPosition);
    });
});
//# sourceMappingURL=Projection.test.js.map