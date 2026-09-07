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
/** Default character when config names none. */
export const DEFAULT_CHARACTER = "bunny";
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
export function resolveCharacterName(config, override) {
    if (override !== null) {
        return override;
    }
    const declared = config.character;
    if (declared === undefined) {
        return DEFAULT_CHARACTER;
    }
    if (typeof declared !== "string" || declared.trim() === "") {
        throw new Error('config: "character" must be a non-empty string');
    }
    return declared;
}
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
function resolveAnimation(animations, required, character) {
    const spec = animations[required.name];
    if (spec === undefined) {
        throw new Error(`character "${character}" is missing animation "${required.name}"`);
    }
    const width = spec.widths[0];
    if (width === undefined) {
        throw new Error(`character "${character}" animation "${required.name}" declares no widths`);
    }
    // generate_sprites.py only suffixes filenames when more than one direction is
    // declared, so "declares two directions" and "produces _left/_right files"
    // are the same condition. Checking it here is what keeps the two in step.
    const declared = spec.directions ?? [];
    const isDirectional = declared.length > 1;
    if (isDirectional !== required.directional) {
        const need = required.directional ? "two directions" : "a single direction";
        throw new Error(`character "${character}" animation "${required.name}" must declare ${need}; ` +
            `the state machine holds ${required.directional ? "left and right frames" : "one frame set"} for it`);
    }
    return {
        animation: required.name,
        width,
        directions: isDirectional ? declared : null,
    };
}
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
export function resolveCharacterAnimations(config, character) {
    const sprite = config.sprites[character];
    if (sprite === undefined) {
        throw new Error(`config.sprites has no character "${character}"`);
    }
    const animations = sprite.animations;
    if (animations === undefined) {
        throw new Error(`config.sprites."${character}" declares no animations`);
    }
    const take = (name, directional) => resolveAnimation(animations, { name, directional }, character);
    // Written out rather than looked up in a table: the field names and the
    // directionality ARE the contract, so a table plus a lookup would only add a
    // not-found arm that can never run.
    return {
        walk: take("walk", true),
        jump: take("jump", true),
        idle: take("idle", true),
        walkToIdle: take("walk_to_idle", true),
        walkToTurnAway: take("walk_to_turn_away", true),
        walkToTurnToward: take("walk_to_turn_toward", true),
        hopAway: take("hop_away", false),
        hopToward: take("hop_toward", false),
    };
}
/** Test hooks for internal functions */
export const _test_hooks = {
    resolveAnimation,
    resolveCharacterName,
    resolveCharacterAnimations,
    DEFAULT_CHARACTER,
};
//# sourceMappingURL=character.js.map