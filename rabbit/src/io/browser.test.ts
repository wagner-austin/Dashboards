/**
 * @vitest-environment jsdom
 * Tests for the browser audio dependency wiring.
 *
 * jsdom implements no Web Audio API, so the constructor is installed on the
 * window for the duration of a test. That is the object the browser supplies,
 * not a stand-in for the code under test — createBrowserAudioContext's own
 * selection logic runs for real.
 */

import { describe, it, expect, afterEach } from "vitest";
import {
  createBrowserAudioContext,
  createDefaultAudioDependencies,
} from "./browser.js";

/** Window as this module reads it, with both vendor spellings optional. */
interface WindowWithWebkit extends Window {
  AudioContext?: unknown;
  webkitAudioContext?: unknown;
}

const win = window as WindowWithWebkit;

afterEach(() => {
  delete win.AudioContext;
  delete win.webkitAudioContext;
});

/** A constructor standing in for the platform's AudioContext. */
function fakeContextClass(tag: string): unknown {
  return class {
    readonly tag = tag;
  };
}

describe("createBrowserAudioContext", () => {
  it("constructs the standard AudioContext when present", () => {
    win.AudioContext = fakeContextClass("standard");

    const context = createBrowserAudioContext() as unknown as { tag: string };

    expect(context.tag).toBe("standard");
  });

  it("constructs the webkit-prefixed one when the standard is absent", () => {
    win.webkitAudioContext = fakeContextClass("webkit");

    const context = createBrowserAudioContext() as unknown as { tag: string };

    expect(context.tag).toBe("webkit");
  });

  it("prefers the standard name when both exist", () => {
    win.AudioContext = fakeContextClass("standard");
    win.webkitAudioContext = fakeContextClass("webkit");

    const context = createBrowserAudioContext() as unknown as { tag: string };

    expect(context.tag).toBe("standard");
  });

  it("throws when the platform supplies neither", () => {
    expect(() => createBrowserAudioContext()).toThrow("Web Audio API not supported");
  });
});

describe("createDefaultAudioDependencies", () => {
  it("wires the context factory to the browser constructor", () => {
    win.AudioContext = fakeContextClass("standard");
    const deps = createDefaultAudioDependencies();

    const context = deps.createContext() as unknown as { tag: string };

    expect(context.tag).toBe("standard");
  });

  it("adds and removes document listeners through the real document", () => {
    const deps = createDefaultAudioDependencies();
    let calls = 0;
    const handler = (): void => {
      calls++;
    };

    deps.addEventListenerFn("click", handler);
    document.dispatchEvent(new Event("click"));
    expect(calls).toBe(1);

    deps.removeEventListenerFn("click", handler);
    document.dispatchEvent(new Event("click"));
    expect(calls).toBe(1);
  });

  it("delegates fetchFn to the platform fetch, passing the url through", async () => {
    const original = globalThis.fetch;
    let requested = "";
    globalThis.fetch = ((url: string): Promise<Response> => {
      requested = url;
      return Promise.resolve({ ok: true } as Response);
    }) as typeof fetch;

    try {
      const deps = createDefaultAudioDependencies();
      const response = await deps.fetchFn("audio/lofi.mp3");

      expect(requested).toBe("audio/lofi.mp3");
      expect(response.ok).toBe(true);
    } finally {
      globalThis.fetch = original;
    }
  });
});
