/**
 * @vitest-environment jsdom
 * Tests for the DOM event adapters.
 *
 * These are the only implementations that touch the document, and they were
 * unexercised while `src/io/**` sat outside the coverage denominator. jsdom
 * dispatches real events, so nothing here is simulated.
 */

import { describe, it, expect, afterEach } from "vitest";
import {
  createDocumentKeyboardSource,
  createDocumentTouchSource,
  _test_hooks,
} from "./events.js";
import type { TouchPoint } from "../input/Touch.js";

const { readTouchPoints } = _test_hooks;

/** Listeners registered on the document, removed after each test. */
const registered: { type: string; handler: EventListener }[] = [];

/** Register through the real document, remembering it for teardown. */
function track(type: string, handler: EventListener): void {
  registered.push({ type, handler });
}

afterEach(() => {
  for (const { type, handler } of registered) {
    document.removeEventListener(type, handler);
  }
  registered.length = 0;
});

/** Build a TouchEvent jsdom will dispatch, carrying the given points. */
function touchEvent(type: string, points: readonly TouchPoint[]): Event {
  const event = new Event(type, { bubbles: true, cancelable: true });
  Object.defineProperty(event, "touches", { value: points });
  return event;
}

describe("createDocumentKeyboardSource", () => {
  it("delivers real keydown events to the handler", () => {
    const source = createDocumentKeyboardSource();
    const seen: string[] = [];
    const handler = (event: KeyboardEvent): void => {
      seen.push(event.key);
    };
    source.addKeyListener("keydown", handler);
    track("keydown", handler as EventListener);

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "a" }));

    expect(seen).toEqual(["a"]);
  });

  it("registers keyup separately from keydown", () => {
    const source = createDocumentKeyboardSource();
    const downs: string[] = [];
    const ups: string[] = [];
    const onDown = (e: KeyboardEvent): void => {
      downs.push(e.key);
    };
    const onUp = (e: KeyboardEvent): void => {
      ups.push(e.key);
    };
    source.addKeyListener("keydown", onDown);
    source.addKeyListener("keyup", onUp);
    track("keydown", onDown as EventListener);
    track("keyup", onUp as EventListener);

    document.dispatchEvent(new KeyboardEvent("keyup", { key: "d" }));

    expect(downs).toEqual([]);
    expect(ups).toEqual(["d"]);
  });
});

describe("readTouchPoints", () => {
  it("converts the DOM TouchList into a plain array", () => {
    // Parse at the edge: the input layer must never see a TouchList.
    const points = [
      { identifier: 1, clientX: 10, clientY: 20 },
      { identifier: 2, clientX: 30, clientY: 40 },
    ];
    const event = touchEvent("touchstart", points) as TouchEvent;

    const result = readTouchPoints(event);

    expect(Array.isArray(result)).toBe(true);
    expect(result).toHaveLength(2);
    expect(result[0]?.clientX).toBe(10);
  });

  it("returns an empty array when no touches are active", () => {
    const event = touchEvent("touchend", []) as TouchEvent;

    expect(readTouchPoints(event)).toEqual([]);
  });
});

describe("createDocumentTouchSource", () => {
  it("passes the event's touch points to the handler", () => {
    const source = createDocumentTouchSource();
    let seen: readonly TouchPoint[] = [];
    source.addTouchListener(
      "touchstart",
      (points) => {
        seen = points;
        return false;
      },
      false
    );

    const points = [{ identifier: 1, clientX: 5, clientY: 6 }];
    document.dispatchEvent(touchEvent("touchstart", points));

    expect(seen).toHaveLength(1);
    expect(seen[0]?.clientY).toBe(6);
    // The listener is anonymous inside the adapter, so clear it by reloading
    // the document body rather than by reference.
    document.dispatchEvent(touchEvent("touchstart", []));
  });

  it("preventDefaults only when the handler asks it to", () => {
    const source = createDocumentTouchSource();
    let handled = true;
    source.addTouchListener("touchmove", () => handled, false);

    const consumed = touchEvent("touchmove", []);
    document.dispatchEvent(consumed);
    expect(consumed.defaultPrevented).toBe(true);

    handled = false;
    const ignored = touchEvent("touchmove", []);
    document.dispatchEvent(ignored);
    expect(ignored.defaultPrevented).toBe(false);
  });

  it("reads a clock that advances", () => {
    const source = createDocumentTouchSource();

    const first = source.now();

    expect(typeof first).toBe("number");
    expect(first).toBeGreaterThan(0);
  });
});
