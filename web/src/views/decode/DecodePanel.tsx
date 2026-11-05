import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import type { ReactElement } from "react";
import { sendJson } from "../../api/client";
import type { Wizard } from "../../api/careTypes";
import type { TaskStart } from "../../api/types";
import { StatusNote } from "../../components/ui/StatusNote";
import { TaskProgress } from "../../components/ui/TaskProgress";
import { useFinished } from "../../hooks/useFinished";
import { useTask } from "../../hooks/useTask";
import ui from "../../styles/ui.module.css";
import { DecodeOutcome } from "./DecodeOutcome";
import { readDecodeResult } from "./readResult";

export function DecodePanel(props: { wizard: Wizard }): ReactElement {
  const [passphrase, setPassphrase] = useState("");
  const [failed, setFailed] = useState(false);
  const task = useTask();
  const result = task.view.status === "done" ? readDecodeResult(task.view.data) : null;
  const decode = useMutation({
    mutationFn: (): Promise<TaskStart> => sendJson<TaskStart>(`/api/decode/sessions/${encodeURIComponent(props.wizard.job_id)}/decode`, "POST", { passphrase, save: true, track: true }),
    onSuccess: (started) => {
      setFailed(false);
      task.start(started.task_id);
    },
  });
  useFinished(task.view, () => setFailed(result === null && task.view.status === "done"));
  const canDecode = props.wizard.readiness.state === "ready" || props.wizard.readiness.state === "parity";
  return (
    <div>
      {props.wizard.passphrase_required ? <label className={ui.field}><span>Passphrase</span><input className={ui.input} type="password" value={passphrase} autoComplete="off" onChange={(event): void => setPassphrase(event.target.value)} /></label> : null}
      <button type="button" className={ui.primary} disabled={!canDecode || task.view.status === "running"} onClick={(): void => decode.mutate()}>Decode</button>
      {decode.isError ? <StatusNote tone="error" title="Decode did not start" detail={decode.error.message} /> : null}
      <TaskProgress view={task.view} />
      {result ? <DecodeOutcome jobId={props.wizard.job_id} result={result} /> : null}
      {failed && !result ? <StatusNote tone="error" title="Decode finished without a file" detail="The task ended before a recovered file was reported." /> : null}
    </div>
  );
}
