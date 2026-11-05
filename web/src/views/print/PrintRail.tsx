import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import type { ReactElement } from "react";
import { Link } from "react-router-dom";
import { getJson, sendJson } from "../../api/client";
import type { PrintersPayload, PrintJobSummary, TaskStart } from "../../api/types";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { QueryGate } from "../../components/ui/QueryGate";
import { SelectField } from "../../components/ui/SelectField";
import { StatusNote } from "../../components/ui/StatusNote";
import { SwitchField } from "../../components/ui/SwitchField";
import { TaskProgress } from "../../components/ui/TaskProgress";
import { useTask } from "../../hooks/useTask";
import { counted, formatWhen, sheetCount } from "../../lib/format";
import { messageOf } from "../../lib/task";
import { useShows } from "../../components/shell/ViewModeContext";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import styles from "../encode/encode.module.css";

export function PrintRail(props: { jobs: PrintJobSummary[]; job: PrintJobSummary; pageCount: number; onJob: (jobId: string) => void }): ReactElement {
  const printers = useQuery({ queryKey: ["printers"], queryFn: (): Promise<PrintersPayload> => getJson<PrintersPayload>("/api/print/printers") });
  return (
    <QueryGate query={printers} loading="Finding printers" errorTitle="The printer list failed">
      {(payload) => <PrintForm jobs={props.jobs} job={props.job} pageCount={props.pageCount} printers={payload} onJob={props.onJob} />}
    </QueryGate>
  );
}

function PrintForm(props: { jobs: PrintJobSummary[]; job: PrintJobSummary; pageCount: number; printers: PrintersPayload; onJob: (jobId: string) => void }): ReactElement {
  const [duplex, setDuplex] = useState(props.job.duplex);
  const [override, setOverride] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const task = useTask();
  const printer = override ?? props.printers.selected ?? props.printers.printers[0]?.uri ?? "";
  const sheets = sheetCount(props.pageCount, duplex);
  const print = useMutation({
    mutationFn: (): Promise<TaskStart> => sendJson<TaskStart>(`/api/print/jobs/${encodeURIComponent(props.job.job_id)}`, "POST", { printer, duplex, confirm: true }),
    onSuccess: (started) => task.start(started.task_id),
  });
  const choosePrinter = useShows("advanced") || props.printers.printers.length > 1;
  const name = props.printers.printers.find((item) => item.uri === printer)?.name || printer || "the printer";
  return (
    <div className={styles.column}>
      <SelectField label="Job" value={props.job.job_id} onValueChange={props.onJob} options={props.jobs.map((job) => ({ value: job.job_id, label: `${job.source_file || job.job_id} · ${formatWhen(job.created)}` }))} />
      {props.printers.printers.length === 0 ? <StatusNote tone="empty" title="No printer found" detail="Connect a printer, then choose it on the Devices desk." /> : null}
      {props.printers.printers.length === 0 ? <Link className={ui.quiet} to="/devices">Open Devices</Link> : null}
      {props.printers.printers.length === 0 ? null : choosePrinter ? <SelectField label="Printer" value={printer} onValueChange={setOverride} options={props.printers.printers.map((item) => ({ value: item.uri, label: item.state ? `${item.name} · ${item.state}` : item.name }))} /> : <p>Printer · {name}</p>}
      <SwitchField label="Print on both sides" checked={duplex} onCheckedChange={setDuplex} />
      <p>{counted(props.pageCount, "page")} · {counted(sheets, "sheet")}</p>
      {props.job.sides === 2 && !duplex ? <p className={view.warn}>This job was laid out for both sides. Printing one side puts the spare pages on their own sheets.</p> : null}
      <button type="button" className={ui.primary} disabled={!printer || task.view.status === "running"} onClick={(): void => setOpen(true)}>Print</button>
      {print.isError ? <StatusNote tone="error" title="Print did not start" detail={print.error.message} /> : null}
      <TaskProgress view={task.view} />
      {task.view.status === "done" ? <p>{messageOf(task.view.data) || "Sent to the printer."} <Link to={`/decode?print_job=${encodeURIComponent(props.job.job_id)}`}>Scan and decode these pages</Link></p> : null}
      <ConfirmDialog open={open} title="Print these pages" body={`Send ${counted(props.pageCount, "page")} to ${name}, ${counted(sheets, "sheet")}, ${duplex ? "duplex" : "single sided"}.`} confirmLabel="Print" onOpenChange={setOpen} onConfirm={(): void => { setOpen(false); print.mutate(); }} />
    </div>
  );
}
