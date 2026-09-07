/**
 * Deciding when to start the engine.
 *
 * Split out of autostart.ts because the decision — start now, or wait for the
 * document — is ordinary logic worth testing, while the line that actually
 * fires it at page load is not. autostart.ts keeps only the latter.
 */
/**
 * Start the engine, now or once the document is ready.
 *
 * A script that runs before the document finishes parsing would find no
 * screen element, so a still-loading document defers the start rather than
 * failing it.
 *
 * Args:
 *     deps: See BootstrapDependencies.
 */
export function bootstrap(deps) {
    const run = () => {
        deps.start().catch(deps.onError);
    };
    if (deps.readyState() === "loading") {
        deps.onDomReady(run);
        return;
    }
    run();
}
//# sourceMappingURL=bootstrap.js.map