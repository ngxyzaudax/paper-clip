import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import type { ReactElement } from "react";
import { useNavigate } from "react-router-dom";
import { queries } from "../../api/queries";
import { sendJson } from "../../api/client";
import type { ScanSummary, TaskStart } from "../../api/types";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { SelectField } from "../../components/ui/SelectField";
import { StatusNote } from "../../components/ui/StatusNote";
import { TaskProgress } from "../../components/ui/TaskProgress";
import { useFinished } from "../../hooks/useFinished";
import { useTask } from "../../hooks/useTask";
import { counted, formatWhen } from "../../lib/format";
import { stringField } from "../../lib/task";
import ui from "../../styles/ui.module.css";
import styles from "../encode/encode.module.css";

export function HealthActions(props: { sha: string }): ReactElement {
  const sessions = useQuery(queries.sessions());
  const [job, setJob] = useState("");
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const task = useTask();
  const rows = sessionsFor(sessions.data ?? [], props.sha);
  const chosen = job || rows[0]?.job_id || "";
  const check = useMutation({
    mutationFn: (): Promise<TaskStart> => sendJson<TaskStart>("/api/health/check", "POST", { scan_job_id: chosen }),
    onSuccess: (started) => task.start(started.task_id),
  });
  const forget = useMutation({
    mutationFn: (): Promise<unknown> => sendJson(`/api/health/${encodeURIComponent(props.sha)}?confirm=true`, "DELETE"),
    onSuccess: () => navigate("/health"),
  });
  useFinished(task.view, () => followSha(stringField(task.view.data, "sha256"), props.sha, navigate));
  return (
    <section className={`${ui.card} ${styles.column}`} aria-label="Check again">
      <p className={ui.kicker}>Check again</p>
      <SelectField label="Scan session" value={chosen} onValueChange={setJob} options={rows.map((session) => ({ value: session.job_id, label: `${formatWhen(session.created)} · ${counted(session.pages, "page")}` }))} />
      <div className={ui.row}>
        <button type="button" className={ui.primary} disabled={!chosen || task.view.status === "running"} onClick={(): void => check.mutate()}>Check</button>
        <button type="button" className={ui.quiet} onClick={(): void => setOpen(true)}>Forget</button>
      </div>
      {rows.length === 0 && sessions.isSuccess ? <StatusNote tone="empty" title="No scans of this file yet" detail="Scan the sheets from the decode desk first." /> : null}
      {sessions.isError ? <StatusNote tone="error" title="Could not list scans" detail={sessions.error.message} onRetry={(): void => void sessions.refetch()} /> : null}
      {check.isError ? <StatusNote tone="error" title="Check did not start" detail={check.error.message} /> : null}
      {forget.isError ? <StatusNote tone="error" title="Could not forget this file" detail={forget.error.message} /> : null}
      <TaskProgress view={task.view} />
      <ConfirmDialog open={open} title="Forget this file" body="Remove the health history for this file." confirmLabel="Forget" onOpenChange={setOpen} onConfirm={(): void => { setOpen(false); forget.mutate(); }} />
    </section>
  );
}

function sessionsFor(rows: ScanSummary[], sha: string): ScanSummary[] {
  const scanned = rows.filter((row) => row.pages > 0);
  return [...scanned.filter((row) => row.sha256 === sha), ...scanned.filter((row) => !row.sha256)];
}

function followSha(found: string, current: string, navigate: (path: string) => void): void {
  if (found && found !== current) navigate(`/health/${found}`);
}
