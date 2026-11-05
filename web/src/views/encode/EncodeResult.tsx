import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { Link } from "react-router-dom";
import { queries } from "../../api/queries";
import { printPages } from "../../components/viewer/artifactPages";
import { PageViewer } from "../../components/viewer/PageViewer";
import { Reveal } from "../../components/ui/Reveal";
import { stringField } from "../../lib/task";
import type { TaskView } from "../../lib/task";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import styles from "./encode.module.css";

export function EncodeResult(props: { view: TaskView; sha: string }): ReactElement | null {
  const jobId = stringField(props.view.data, "job_id");
  if (!jobId) return <StreamingThumbs urls={props.view.thumbs} />;
  return (
    <section className={ui.card} aria-label="Encoded pages">
      <div className={styles.column}>
        <p className={ui.kicker}>Saved printout</p>
        <Reveal at="expert"><p className={view.caption}>Reference code {jobId}</p></Reveal>
        <JobPages jobId={jobId} />
        <div className={ui.row}>
          <Link className={ui.primary} to={`/print?job=${encodeURIComponent(jobId)}`}>Print</Link>
          <Link className={ui.quiet} to={`/decode?print_job=${encodeURIComponent(jobId)}`}>Scan and decode</Link>
          {props.sha ? <Link className={ui.quiet} to={`/library/${props.sha}`}>Library</Link> : null}
          <Link className={ui.quiet} to={`/archive/print/${encodeURIComponent(jobId)}`}>Archive</Link>
        </div>
      </div>
    </section>
  );
}

function JobPages(props: { jobId: string }): ReactElement | null {
  const job = useQuery(queries.printJob(props.jobId));
  if (!job.data) return null;
  return <PageViewer pages={printPages(job.data.job_id, job.data.page_names, job.data.data_pages)} />;
}

function StreamingThumbs(props: { urls: string[] }): ReactElement | null {
  if (props.urls.length === 0) return null;
  return (
    <div className={styles.sheets} aria-label="Pages rendered so far">
      {props.urls.map((url, index) => <img key={url} src={url} alt={`Encoded page ${index + 1}`} width={72} />)}
    </div>
  );
}
