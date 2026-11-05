import type { CSSProperties, ReactElement } from "react";
import type { TaskView } from "../../lib/task";
import controls from "../../styles/controls.module.css";
import { StatusNote } from "./StatusNote";

export function TaskProgress(props: { view: TaskView }): ReactElement | null {
  if (props.view.status === "idle") return null;
  if (props.view.status === "error") return <StatusNote tone="error" title="The task stopped" detail={props.view.error} />;
  return (
    <div>
      <div className={controls.track} role="progressbar" aria-label={props.view.label || "Task progress"} aria-valuenow={percent(props.view.progress)} aria-valuemin={0} aria-valuemax={100}>
        <div className={props.view.progress === null ? controls.indeterminate : controls.fill} style={fillStyle(props.view.progress)} />
      </div>
      {props.view.label ? <p>{props.view.label}</p> : null}
    </div>
  );
}

function percent(progress: number | null): number | undefined {
  if (progress === null) return undefined;
  return Math.round(Math.max(0, Math.min(1, progress)) * 100);
}

function fillStyle(progress: number | null): CSSProperties | undefined {
  const value = percent(progress);
  if (value === undefined) return undefined;
  return { width: `${value}%` };
}
