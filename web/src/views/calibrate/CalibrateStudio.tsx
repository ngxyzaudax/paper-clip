import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import type { ReactElement } from "react";
import { sendJson } from "../../api/client";
import type { CalibrateState } from "../../api/careTypes";
import type { TaskStart } from "../../api/types";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { StatusNote } from "../../components/ui/StatusNote";
import { TaskProgress } from "../../components/ui/TaskProgress";
import { useFinished } from "../../hooks/useFinished";
import { useTask } from "../../hooks/useTask";
import { messageOf } from "../../lib/task";
import view from "../../styles/view.module.css";
import { CalibrateActions } from "./CalibrateActions";
import { CalibrateReport } from "./CalibrateReport";
import { CalibrateSheets } from "./CalibrateSheets";

const CONFIRM: Record<string, { title: string; body: string; label: string }> = {
  print: { title: "Print the sheet", body: "Send the calibration sheet to the saved printer.", label: "Print" },
  save: { title: "Save the profile", body: "Replace the press profile with the chosen density.", label: "Save profile" },
  new: { title: "New session", body: "Archive this session and clear the bench.", label: "Start new" },
};

export function CalibrateStudio(props: { state: CalibrateState; onRefresh: () => void }): ReactElement {
  const [pending, setPending] = useState<string | null>(null);
  const task = useTask();
  const run = useMutation({
    mutationFn: (action: { name: string; confirm: boolean }): Promise<TaskStart> => sendJson<TaskStart>(`/api/calibrate/${action.name}`, "POST", action.confirm ? { confirm: true } : undefined),
    onSuccess: (started) => task.start(started.task_id),
  });
  useFinished(task.view, props.onRefresh);
  const busy = run.isPending || task.view.status === "running";
  const copy = pending ? CONFIRM[pending] : undefined;
  return (
    <div className={view.stack}>
      <CalibrateActions busy={busy} onAsk={(name): void => ask(name, setPending, run.mutate)} />
      {run.isError ? <StatusNote tone="error" title="The step did not start" detail={run.error.message} /> : null}
      <TaskProgress view={task.view} />
      {task.view.status === "done" ? <pre>{messageOf(task.view.data) || "Finished."}</pre> : null}
      <CalibrateSheets state={props.state} />
      <CalibrateReport state={props.state} />
      <ConfirmDialog open={Boolean(copy)} title={copy?.title ?? ""} body={copy?.body ?? ""} confirmLabel={copy?.label ?? "Confirm"} onOpenChange={(open): void => { if (!open) setPending(null); }} onConfirm={(): void => confirm(pending, setPending, run.mutate)} />
    </div>
  );
}

function ask(name: string, setPending: (name: string | null) => void, run: (action: { name: string; confirm: boolean }) => void): void {
  if (name in CONFIRM) setPending(name);
  else run({ name, confirm: false });
}

function confirm(pending: string | null, setPending: (name: string | null) => void, run: (action: { name: string; confirm: boolean }) => void): void {
  if (pending) run({ name: pending, confirm: true });
  setPending(null);
}
