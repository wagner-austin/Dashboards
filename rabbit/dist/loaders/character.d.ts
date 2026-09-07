/**
 * Resolving which character the scene draws, and where its frames live.
 *
 * The engine used to name "bunny" and its eight frame widths directly in the
 * loader, so a second character could not be added without editing code. Both
 * now come from config.json, and this module is the only place that reads
 * them.
 *
 * It also enforces the coupling that previously had nowhere to live. The
 * character state machine holds left and right frames for six animations and a
 * single set for the two depth hops, so config must declare exactly that shape.
 * When it did not, generate_sprites.py emitted a bare `w40.ts` while the loader
 * asked for `w40_left.js` — a mismatch nothing detected until the sprite 404'd
 * in the browser. Here it is a startup error naming the animation.
 */
import type { Config, Direction, SpriteAnimationConfig } from "../types.js";
/**
 * One animation's resolved location on disk.
 *
 * animation: Animation name, matching the config key and the directory name.
 * width: Character width to load, the first width the animation declares.
 * directions: Left/right variants to load, or null for a single undirected set.
 */
export interface AnimationSource {
    readonly animation: string;
    readonly width: number;
    readonly directions: readonly Direction[] | null;
}
/**
 * An animation the character state machine drives, and the shape it needs.
 *
 * `directional` is not a preference read from config — it is what
 * `BunnyFrames` structurally holds. Six animations carry left and right
 * fields; the two depth hops carry one set each, because the character is
 * facing away from or toward the camera and has no side.
 */
interface RequiredAnimation {
    readonly name: string;
    readonly directional: boolean;
}
/**
 * Every animation source a character needs, one named field each.
 *
 * A record rather than a list because the caller wants them by name. Returning
 * a list made the loader look each one up again, and a lookup needs a
 * not-found arm that cannot happen — the list it searches is the one this
 * module just built. Naming the fields deletes that unreachable branch instead
 * of leaving it to be covered by a test asserting something impossible.
 */
export interface CharacterSources {
    readonly walk: AnimationSource;
    readonly jump: AnimationSource;
    readonly idle: AnimationSource;
    readonly walkToIdle: AnimationSource;
    readonly walkToTurnAway: AnimationSource;
    readonly walkToTurnToward: AnimationSource;
    readonly hopAway: AnimationSource;
    readonly hopToward: AnimationSource;
}
/** Default character when config names none. */
export declare const DEFAULT_CHARACTER = "bunny";
/**
 * Decide which character to draw.
 *
 * The override exists so a candidate character can be viewed in the real
 * scene, at its real size, behind the real trees, before its art is committed
 * — which a grid of isolated frames cannot show. It is deliberately not a
 * fallback: an override that names nothing resolvable fails in
 * resolveCharacterAnimations rather than quietly reverting to the default.
 *
 * Args:
 *     config: Application config.
 *     override: Character name from the page URL, or null when absent.
 *
 * Returns:
 *     The character name to load.
 *
 * Raises:
 *     Error: If config carries a `character` field that is not a string.
 */
export declare function resolveCharacterName(config: Config, override: string | null): string;
/**
 * Read one animation's config entry, checking it can actually be loaded.
 *
 * Args:
 *     animations: The character's animations block.
 *     required: The animation being resolved and the shape it must have.
 *     character: Character name, for error messages.
 *
 * Returns:
 *     The resolved AnimationSource.
 *
 * Raises:
 *     Error: If the animation is absent, declares no widths, or declares a
 *         directionality the state machine cannot consume.
 */
declare function resolveAnimation(animations: Record<string, SpriteAnimationConfig>, required: RequiredAnimation, character: string): AnimationSource;
/**
 * Resolve every animation a character needs, or explain what is missing.
 *
 * Args:
 *     config: Application config.
 *     character: Character name, as returned by resolveCharacterName.
 *
 * Returns:
 *     One AnimationSource per required animation.
 *
 * Raises:
 *     Error: If the character is absent from config, declares no animations,
 *         or any required animation is missing or mis-shaped.
 */
export declare function resolveCharacterAnimations(config: Config, character: string): CharacterSources;
/** Test hooks for internal functions */
export declare const _test_hooks: {
    resolveAnimation: typeof resolveAnimation;
    resolveCharacterName: typeof resolveCharacterName;
    resolveCharacterAnimations: typeof resolveCharacterAnimations;
    DEFAULT_CHARACTER: string;
};
export {};
//# sourceMappingURL=character.d.ts.map