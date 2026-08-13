import "@testing-library/jest-dom/vitest";

// Pin the UI language for tests (task 0040) to English deterministically — set before any module
// imports i18n, so its detector reads this instead of jsdom's navigator.
localStorage.setItem("dyr_lang", "en");

// jsdom does not implement ResizeObserver, which assistant-ui's viewport/composer use via
// refs. Stub it so <App /> mounts as it would in a real browser; the stub is inert.
class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
}
globalThis.ResizeObserver ??= ResizeObserverStub as unknown as typeof ResizeObserver;

// jsdom stubs Element.scrollTo as a no-op-less missing method; assistant-ui's viewport
// autoscroll calls it in an animation frame. Provide a no-op so it doesn't throw.
if (!Element.prototype.scrollTo) {
    Element.prototype.scrollTo = () => {};
}
