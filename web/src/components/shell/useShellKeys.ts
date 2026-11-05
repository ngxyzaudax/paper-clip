import { useEffect } from "react";
import { blockedTarget } from "../../lib/keys";
import { VIEW_MODES } from "../../lib/viewMode";
import type { ViewMode } from "../../lib/viewMode";

export function useShellKeys(openPalette: () => void, openHelp: () => void, setMode: (mode: ViewMode) => void): void {
  useEffect(() => {
    function onKey(event: KeyboardEvent): void {
      if (isPalette(event)) {
        event.preventDefault();
        openPalette();
        return;
      }
      const mode = modeKey(event);
      if (mode) {
        event.preventDefault();
        setMode(mode);
        return;
      }
      if (event.key === "?" && !blockedTarget(event.target)) {
        event.preventDefault();
        openHelp();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [openPalette, openHelp, setMode]);
}

function isPalette(event: KeyboardEvent): boolean {
  return (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";
}

function modeKey(event: KeyboardEvent): ViewMode | null {
  if (!event.altKey || event.metaKey || event.ctrlKey) return null;
  const digit = /^Digit([1-3])$/.exec(event.code);
  return digit ? VIEW_MODES[Number(digit[1]) - 1]?.mode ?? null : null;
}
