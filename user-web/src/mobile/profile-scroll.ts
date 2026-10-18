type Position = { left?: number; top?: number };

// A fresh profile has no private lists until its requests finish. Restoring earlier
// clamps a saved position to that temporary, shorter document.
export function restoreProfileScroll(
  position: Position,
  isCurrent: () => boolean,
  onNavigation: (cancel: () => void) => () => void,
): Promise<Position | false> {
  return new Promise((resolve) => {
    let finished = false;
    let removeGuard = () => {};
    let timer: ReturnType<typeof setTimeout>;
    const observer = new MutationObserver(check);
    function finish(value: Position | false) {
      if (finished) return;
      finished = true;
      observer.disconnect();
      removeGuard();
      clearTimeout(timer);
      resolve(value);
    }
    function check() {
      if (!isCurrent()) finish(false);
      else if (
        document.querySelector('.profile-page[data-profile-ready="true"]')
      )
        finish(position);
    }
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["data-profile-ready"],
    });
    removeGuard = onNavigation(() => finish(false));
    // The API helper times out after 20 seconds; never retain an observer forever.
    timer = setTimeout(() => finish(false), 22000);
    check();
  });
}
