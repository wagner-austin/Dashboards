/**
 * @vitest-environment jsdom
 * Tests for the sprite transport: URL resolution, import caching, validation.
 *
 * This suite exists because `src/io/**` used to sit outside the coverage
 * denominator on the grounds that it was "tested through dependency
 * injection". It was not: DI meant main.ts's tests substituted fakes, so these
 * implementations never ran, and the 100% report was measuring a codebase with
 * 340 lines removed from it.
 */
export {};
//# sourceMappingURL=transport.test.d.ts.map