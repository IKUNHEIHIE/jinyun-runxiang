type Position = { left?: number; top?: number; behavior?: ScrollBehavior };

// Out-in transitions temporarily leave the old page (or no page) in the document.
// Back navigation also needs the incoming page's async content before restoration.
export function restorePageScroll(
  position: Position,
  fullPath: string,
  restoring: boolean,
  isCurrent: () => boolean,
  onNavigation: (cancel: () => void) => () => void,
): Promise<Position | false> {
  return new Promise((resolve) => {
    let finished = false;
    let removeGuard = () => {};
    let timer: ReturnType<typeof setTimeout>;
    const observer = new MutationObserver(check);
    const interrupt = () => finish(false);
    const interactions = ['pointerdown', 'touchstart', 'wheel', 'keydown'];
    function finish(value: Position | false) {
      if (finished) return;
      finished = true;
      observer.disconnect();
      removeGuard();
      clearTimeout(timer);
      interactions.forEach((name) => document.removeEventListener(name, interrupt, true));
      resolve(value);
    }
    function check() {
      if (!isCurrent()) finish(false);
      else {
        const view = document.querySelector<HTMLElement>('[data-route-view]');
        if (!view || view.getAttribute('data-route-view') !== fullPath) return;
        if (Array.from(view.classList).some((name) => /^page-.*-(enter|leave)-active$/.test(name))) return;
        if (restoring && (
          view.getAttribute('data-profile-ready') === 'false' ||
          view.getAttribute('data-page-ready') === 'false' ||
          view.querySelector('.async-state[aria-busy="true"]')
        )) return;
        finish({ ...position, behavior: 'instant' });
      }
    }
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["data-profile-ready", "data-page-ready", "data-route-view", "aria-busy", "class"],
    });
    removeGuard = onNavigation(() => finish(false));
    interactions.forEach((name) => document.addEventListener(name, interrupt, { capture: true, passive: true }));
    // The API helper times out after 20 seconds; never retain an observer forever.
    timer = setTimeout(() => finish(false), 22000);
    check();
  });
}
