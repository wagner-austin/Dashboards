/**
 * @vitest-environment jsdom
 * Tests for the browser audio dependency wiring.
 *
 * jsdom implements no Web Audio API, so the constructor is installed on the
 * window for the duration of a test. That is the object the browser supplies,
 * not a stand-in for the code under test — createBrowserAudioContext's own
 * selection logic runs for real.
 */
export {};
//# sourceMappingURL=browser.test.d.ts.map