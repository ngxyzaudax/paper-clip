const VIEW_MODE_KEY = "paper-clip-view-mode";

export type ViewMode = "simple" | "advanced" | "expert";

export const VIEW_MODES: readonly { mode: ViewMode; label: string; detail: string }[] = [
  { mode: "simple", label: "Simple", detail: "The essentials. Sensible defaults handle the rest." },
  { mode: "advanced", label: "Advanced", detail: "More control over the print and each scan." },
  { mode: "expert", label: "Expert", detail: "Every setting, plus the technical details." },
];

const RANK: Record<ViewMode, number> = { simple: 0, advanced: 1, expert: 2 };

export function isViewMode(value: unknown): value is ViewMode {
  return value === "simple" || value === "advanced" || value === "expert";
}

export function shows(current: ViewMode, needed: ViewMode): boolean {
  return RANK[current] >= RANK[needed];
}

export function storedViewMode(): ViewMode {
  try {
    const value = localStorage.getItem(VIEW_MODE_KEY);
    return isViewMode(value) ? value : "simple";
  } catch {
    return "simple";
  }
}

export function storeViewMode(mode: ViewMode): void {
  try {
    localStorage.setItem(VIEW_MODE_KEY, mode);
  } catch {
    return;
  }
}
