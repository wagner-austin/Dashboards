/**
 * @vitest-environment jsdom
 * Tests for fetching and decoding config.json.
 */

import { describe, it, expect, afterEach } from "vitest";
import { loadConfig } from "./config-io.js";
import { _test_hooks as transportHooks } from "./transport.js";
import { createTestConfig } from "../testing/io-fixtures.js";

const realFetch = transportHooks.fetchFn;

afterEach(() => {
  transportHooks.fetchFn = realFetch;
});

describe("loadConfig", () => {
  it("fetches config.json and returns the decoded document", async () => {
    const config = createTestConfig();
    let fetched = "";
    transportHooks.fetchFn = (url: string): Promise<Response> => {
      fetched = url;
      return Promise.resolve({ json: () => Promise.resolve(config) } as Response);
    };

    const result = await loadConfig();

    expect(fetched).toContain("config.json");
    expect(result.settings.fps).toBe(60);
  });

  it("resolves config.json against the page", async () => {
    let fetched = "";
    transportHooks.fetchFn = (url: string): Promise<Response> => {
      fetched = url;
      return Promise.resolve({
        json: () => Promise.resolve(createTestConfig()),
      } as Response);
    };

    await loadConfig();

    expect(new URL(fetched).origin).toBe(new URL(document.baseURI).origin);
  });

  it("rejects a document that fails validation", async () => {
    transportHooks.fetchFn = (): Promise<Response> =>
      Promise.resolve({ json: () => Promise.resolve({ sprites: {} }) } as Response);

    await expect(loadConfig()).rejects.toThrow("Invalid config");
  });
});
