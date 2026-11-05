import { useMutation, useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { queries } from "../../api/queries";
import { sendForm, sendJson } from "../../api/client";
import type { Wizard } from "../../api/careTypes";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import { StatusNote } from "../../components/ui/StatusNote";
import { useFileDrop } from "../../hooks/useFileDrop";
import { classes } from "../../lib/classes";
import { counted, formatWhen } from "../../lib/format";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import drop from "../encode/encode.module.css";

export function DecodeSourcePage(): ReactElement {
  const [params] = useSearchParams();
  const printJob = params.get("print_job") ?? "";
  const sessions = useQuery(queries.sessions());
  return (
    <section className={view.stack}>
      <PageHeader kicker="Workflow" title="Scan and decode" lede="Put any page face down. The sheet tells this desk which page it is, and what to scan next." />
      <SourceActions printJob={printJob} />
      <QueryGate query={sessions} loading="Looking for sessions" errorTitle="Scan sessions failed" isEmpty={(rows) => rows.length === 0} empty={<StatusNote tone="empty" title="No scan sessions" detail="Scan a sheet or drop images." />}>
        {(rows) => (
          <div className={view.list}>
            {rows.map((session) => <Link key={session.job_id} to={`/decode/${session.job_id}`}>{counted(session.pages, "scan")} · {formatWhen(session.created)}</Link>)}
          </div>
        )}
      </QueryGate>
    </section>
  );
}

function SourceActions(props: { printJob: string }): ReactElement {
  const navigate = useNavigate();
  const scan = useMutation({ mutationFn: (): Promise<Wizard> => openSession(props.printJob), onSuccess: (wizard) => navigate(`/decode/${wizard.job_id}`) });
  const upload = useMutation({ mutationFn: (files: File[]): Promise<string> => uploadImages(files, props.printJob), onSuccess: (jobId) => navigate(`/decode/${jobId}`) });
  const files = useFileDrop(upload.mutate);
  return (
    <div className={view.split}>
      <div className={drop.column}>
        <button type="button" className={ui.primary} disabled={scan.isPending} onClick={(): void => scan.mutate()}>Scan now</button>
        {scan.isError ? <StatusNote tone="error" title="Could not open a session" detail={scan.error.message} /> : null}
      </div>
      <label className={classes(drop.drop, files.hot && drop.hot)} {...files.zone}>
        <input className={drop.file} type="file" accept="image/*" multiple onChange={files.onInput} />
        <strong>Drop scan images</strong>
        <span>One image per side</span>
      </label>
      {upload.isPending ? <StatusNote tone="busy" title="Uploading scans" /> : null}
      {upload.isError ? <StatusNote tone="error" title="Upload failed" detail={upload.error.message} /> : null}
    </div>
  );
}

function openSession(printJob: string): Promise<Wizard> {
  return sendJson<Wizard>("/api/decode/sessions", "POST", { print_job_id: printJob });
}

async function uploadImages(files: File[], printJob: string): Promise<string> {
  const session = await openSession(printJob);
  const body = new FormData();
  files.forEach((file) => body.append("files", file));
  await sendForm(`/api/decode/sessions/${encodeURIComponent(session.job_id)}/upload`, body);
  return session.job_id;
}
