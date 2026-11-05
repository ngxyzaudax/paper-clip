import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactElement, ReactNode } from "react";
import { shows, storeViewMode, storedViewMode } from "../../lib/viewMode";
import type { ViewMode } from "../../lib/viewMode";

type ViewModeState = { mode: ViewMode; setMode: (mode: ViewMode) => void };

const ViewModeContext = createContext<ViewModeState>({ mode: "simple", setMode: (): void => undefined });

export function ViewModeProvider(props: { children: ReactNode }): ReactElement {
  const [mode, setState] = useState<ViewMode>(storedViewMode);
  const setMode = useCallback((next: ViewMode): void => {
    storeViewMode(next);
    setState(next);
  }, []);
  const value = useMemo(() => ({ mode, setMode }), [mode, setMode]);
  return <ViewModeContext.Provider value={value}>{props.children}</ViewModeContext.Provider>;
}

export function useViewMode(): ViewModeState {
  return useContext(ViewModeContext);
}

export function useShows(needed: ViewMode): boolean {
  return shows(useViewMode().mode, needed);
}
