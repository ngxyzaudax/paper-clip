import type { ReactElement, ReactNode } from "react";
import type { ViewMode } from "../../lib/viewMode";
import { useShows } from "../shell/ViewModeContext";

export function Reveal(props: { at: ViewMode; children: ReactNode }): ReactElement | null {
  return useShows(props.at) ? <>{props.children}</> : null;
}
