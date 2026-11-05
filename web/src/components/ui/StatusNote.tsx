import type { ReactElement } from "react";
import { classes } from "../../lib/classes";
import note from "../../styles/note.module.css";
import ui from "../../styles/ui.module.css";

export function StatusNote(props: { tone: "empty" | "busy" | "error"; title: string; detail?: string; onRetry?: () => void }): ReactElement {
  return (
    <div className={classes(note.note, note[props.tone])} role={props.tone === "error" ? "alert" : "status"}>
      <span className={note.mark} />
      <p className={note.title}>{props.title}</p>
      {props.detail ? <p className={note.detail}>{props.detail}</p> : null}
      {props.onRetry ? <button type="button" className={classes(ui.quiet, note.retry)} onClick={props.onRetry}>Retry</button> : null}
    </div>
  );
}
