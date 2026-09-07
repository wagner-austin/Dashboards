/**
 * Tests for character resolution from config.
 */
import { describe, it, expect } from "vitest";
import { resolveCharacterName, resolveCharacterAnimations, DEFAULT_CHARACTER, _test_hooks, } from "./character.js";
import { DEFAULT_AUTORUN_CONFIG } from "../input/index.js";
const { resolveAnimation } = _test_hooks;
/** Build one animation entry with the given directionality. */
function anim(directional, widths = [40]) {
    return {
        source: "originals/x.gif",
        widths,
        contrast: 1.4,
        invert: true,
        ...(directional ? { directions: ["left", "right"] } : {}),
    };
}
/** Build a complete, valid animations block for a character. */
function completeAnimations() {
    return {
        walk: anim(true, [50]),
        jump: anim(true, [50]),
        idle: anim(true),
        walk_to_idle: anim(true),
        walk_to_turn_away: anim(true),
        walk_to_turn_toward: anim(true),
        hop_away: anim(false),
        hop_toward: anim(false),
    };
}
/** Build a config carrying the given sprites. */
function configWith(sprites, character) {
    return {
        sprites,
        layers: [],
        settings: {
            fps: 60,
            scrollSpeed: 90,
            depthSpeed: 30,
            animation: { walk: 120, idle: 500, jump: 58, transition: 85, hop: 150 },
        },
        autorun: DEFAULT_AUTORUN_CONFIG,
        ...(character !== undefined ? { character } : {}),
    };
}
describe("resolveCharacterName", () => {
    it("defaults to the bunny when config names no character", () => {
        expect(resolveCharacterName(configWith({}), null)).toBe(DEFAULT_CHARACTER);
        expect(DEFAULT_CHARACTER).toBe("bunny");
    });
    it("reads the character config declares", () => {
        expect(resolveCharacterName(configWith({}, "lion"), null)).toBe("lion");
    });
    it("lets the override win over config", () => {
        expect(resolveCharacterName(configWith({}, "bunny"), "lion")).toBe("lion");
    });
    it("lets the override win over the default", () => {
        expect(resolveCharacterName(configWith({}), "lion")).toBe("lion");
    });
    it("rejects a non-string character", () => {
        expect(() => resolveCharacterName(configWith({}, 7), null)).toThrow('config: "character" must be a non-empty string');
    });
    it("rejects an empty character", () => {
        expect(() => resolveCharacterName(configWith({}, "  "), null)).toThrow('config: "character" must be a non-empty string');
    });
});
describe("resolveCharacterAnimations", () => {
    it("resolves every animation the state machine drives", () => {
        const config = configWith({ bunny: { animations: completeAnimations() } });
        const resolved = resolveCharacterAnimations(config, "bunny");
        // The field names are the contract; each must name its config animation.
        expect(resolved.walk.animation).toBe("walk");
        expect(resolved.jump.animation).toBe("jump");
        expect(resolved.idle.animation).toBe("idle");
        expect(resolved.walkToIdle.animation).toBe("walk_to_idle");
        expect(resolved.walkToTurnAway.animation).toBe("walk_to_turn_away");
        expect(resolved.walkToTurnToward.animation).toBe("walk_to_turn_toward");
        expect(resolved.hopAway.animation).toBe("hop_away");
        expect(resolved.hopToward.animation).toBe("hop_toward");
    });
    it("takes the first declared width", () => {
        const animations = completeAnimations();
        animations.idle = anim(true, [40, 80]);
        const config = configWith({ bunny: { animations } });
        expect(resolveCharacterAnimations(config, "bunny").idle.width).toBe(40);
    });
    it("carries directions for directional animations and null for the hops", () => {
        const config = configWith({ bunny: { animations: completeAnimations() } });
        const resolved = resolveCharacterAnimations(config, "bunny");
        expect(resolved.walk.directions).toEqual(["left", "right"]);
        expect(resolved.hopAway.directions).toBeNull();
        expect(resolved.hopToward.directions).toBeNull();
    });
    it("rejects a character absent from config", () => {
        expect(() => resolveCharacterAnimations(configWith({}), "lion")).toThrow('config.sprites has no character "lion"');
    });
    it("rejects a sprite with no animations block", () => {
        const config = configWith({ tree1: { source: "t.gif", widths: [15] } });
        expect(() => resolveCharacterAnimations(config, "tree1")).toThrow('config.sprites."tree1" declares no animations');
    });
    it("names the animation that is missing", () => {
        const animations = completeAnimations();
        delete animations.hop_toward;
        const config = configWith({ lion: { animations } });
        expect(() => resolveCharacterAnimations(config, "lion")).toThrow('character "lion" is missing animation "hop_toward"');
    });
    it("rejects an animation declaring no widths", () => {
        const animations = completeAnimations();
        animations.walk = anim(true, []);
        const config = configWith({ lion: { animations } });
        expect(() => resolveCharacterAnimations(config, "lion")).toThrow('character "lion" animation "walk" declares no widths');
    });
    it("rejects a directional animation declared without directions", () => {
        // This is the orphan bug: the generator emits a bare w40.ts while the
        // loader asks for w40_left.js, and nothing noticed until the 404.
        const animations = completeAnimations();
        animations.walk_to_turn_away = anim(false);
        const config = configWith({ lion: { animations } });
        expect(() => resolveCharacterAnimations(config, "lion")).toThrow(/animation "walk_to_turn_away" must declare two directions/);
    });
    it("rejects a hop declared with two directions", () => {
        const animations = completeAnimations();
        animations.hop_away = anim(true);
        const config = configWith({ lion: { animations } });
        expect(() => resolveCharacterAnimations(config, "lion")).toThrow(/animation "hop_away" must declare a single direction/);
    });
    it("treats a single declared direction as undirected", () => {
        // generate_sprites.py only suffixes when more than one direction is
        // declared, so ["left"] produces w40.ts, not w40_left.ts.
        const animations = completeAnimations();
        animations.hop_away = {
            source: "originals/x.gif",
            widths: [40],
            contrast: 1.4,
            invert: true,
            directions: ["left"],
        };
        const config = configWith({ lion: { animations } });
        expect(resolveCharacterAnimations(config, "lion").hopAway.directions).toBeNull();
    });
});
describe("resolveAnimation", () => {
    it("names the character in its errors", () => {
        expect(() => resolveAnimation({}, { name: "walk", directional: true }, "lion")).toThrow('character "lion" is missing animation "walk"');
    });
});
//# sourceMappingURL=character.test.js.map