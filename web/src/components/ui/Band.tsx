import type { ReactElement } from "react";
import note from "../../styles/note.module.css";

const COLORS: Record<string, string> = {
  Healthy: "var(--healthy)",
  Worn: "var(--worn)",
  "At risk": "var(--risk)",
  Critical: "var(--critical)",
  Lost: "var(--lost)",
};

export function Band(props: { status: string }): ReactElement {
  return (
    <span className={note.band}>
      <i className={note.dot} style={{ background: COLORS[props.status] ?? "var(--muted)" }} />
      {props.status || "Unknown"}
    </span>
  );
}
