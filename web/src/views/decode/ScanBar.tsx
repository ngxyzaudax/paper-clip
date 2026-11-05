import { useMutation } from "@tanstack/react-query";
import { useEffect } from "react";
import type { ReactElement } from "react";
import { sendJson } from "../../api/client";
import type { TaskStart } from "../../api/types";
import { TaskProgress } from "../../components/ui/TaskProgress";
import { StatusNote } from "../../components/ui/StatusNote";
import { useTask } from "../../hooks/useTask";
import { useFinished } from "../../hooks/useFinished";
import { blockedTarget, buttonTarget, dialogOpen } from "../../lib/keys";
import ui from "../../styles/ui.module.css";

export function ScanBar(props: { jobId: string; onChanged: () => void }): ReactElement {
  const task = useTask();
  const capture = useMutation({
    mutationFn: (): Promise<TaskStart> => sendJson<TaskStart>(`/api/decode/sessions/${encodeURIComponent(props.jobId)}/capture`, "POST"),
    onSuccess: (started) => task.start(started.task_id),
  });
  const busy = capture.isPending || task.view.status === "running";
  const start = capture.mutate;
  useFinished(task.view, props.onChanged);
  useEffect(() => {
    function onKey(event: KeyboardEvent): void {
      if (event.key !== " " || event.repeat || busy || dialogOpen() || blockedTarget(event.target) || buttonTarget(event.target)) return;
      event.preventDefault();
      start();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [busy, start]);
  return (
    <div>
      <button type="button" className={ui.primary} disabled={busy} onClick={(): void => start()}>Scan next</button>
      <span className={ui.hintKey}>or press Space</span>
      {capture.isError ? <StatusNote tone="error" title="Scan did not start" detail={capture.error.message} /> : null}
      <TaskProgress view={task.view} />
    </div>
  );
}
