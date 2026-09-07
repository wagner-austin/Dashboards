/**
 * Deciding when to start the engine.
 *
 * Split out of autostart.ts because the decision — start now, or wait for the
 * document — is ordinary logic worth testing, while the line that actually
 * fires it at page load is not. autostart.ts keeps only the latter.
 */

/**
 * What bootstrap needs from the page.
 *
 * readyState: The document's current ready state.
 * onDomReady: Register a callback for DOMContentLoaded.
 * start: Begin the engine. Rejections are reported, never swallowed.
 * onError: Report a failed start.
 */
export interface BootstrapDependencies {
  readonly readyState: () => DocumentReadyState;
  readonly onDomReady: (handler: () => void) => void;
  readonly start: () => Promise<void>;
  readonly onError: (error: unknown) => void;
}

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
export function bootstrap(deps: BootstrapDependencies): void {
  const run = (): void => {
    deps.start().catch(deps.onError);
  };

  if (deps.readyState() === "loading") {
    deps.onDomReady(run);
    return;
  }
  run();
}
