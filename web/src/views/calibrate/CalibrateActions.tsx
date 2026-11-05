import type { ReactElement } from "react";
import { useViewMode } from "../../components/shell/ViewModeContext";
import { shows } from "../../lib/viewMode";
import type { ViewMode } from "../../lib/viewMode";
import ui from "../../styles/ui.module.css";

const ACTIONS: { name: string; label: string; level: ViewMode }[] = [
  { name: "sheet", label: "Render sheet", level: "simple" },
  { name: "simulate", label: "Simulate", level: "expert" },
  { name: "print", label: "Print", level: "simple" },
  { name: "scan", label: "Scan view", level: "simple" },
  { name: "save", label: "Save profile", level: "simple" },
  { name: "new", label: "New session", level: "advanced" },
];

export function CalibrateActions(props: { busy: boolean; onAsk: (name: string) => void }): ReactElement {
  const mode = useViewMode().mode;
  return (
    <div className={ui.row}>
      {ACTIONS.filter((action) => shows(mode, action.level)).map((action) => (
        <button key={action.name} type="button" className={action.name === "save" ? ui.primary : ui.quiet} disabled={props.busy} onClick={(): void => props.onAsk(action.name)}>
          {action.label}
        </button>
      ))}
    </div>
  );
}
