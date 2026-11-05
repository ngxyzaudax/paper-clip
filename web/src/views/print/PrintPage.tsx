import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import type { ReactElement } from "react";
import { queries } from "../../api/queries";
import type { PrintJobSummary } from "../../api/types";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import { PageViewer } from "../../components/viewer/PageViewer";
import { StatusNote } from "../../components/ui/StatusNote";
import view from "../../styles/view.module.css";
import { printPages } from "../../components/viewer/artifactPages";
import { PrintRail } from "./PrintRail";

export function PrintPage(): ReactElement {
  const jobs = useQuery(queries.printJobs());
  return (
    <section className={view.stack}>
      <PageHeader kicker="Workflow" title="Print" lede="Send a finished sheet to the printer. Printing both sides uses half as many sheets." />
      <QueryGate query={jobs} loading="Looking for jobs" errorTitle="Print jobs failed" isEmpty={(rows) => rows.length === 0} empty={<StatusNote tone="empty" title="No print jobs" detail="Turn a file into sheets before printing." />}>
        {(rows) => <PrintDesk jobs={rows} />}
      </QueryGate>
    </section>
  );
}

function PrintDesk(props: { jobs: PrintJobSummary[] }): ReactElement {
  const [params, setParams] = useSearchParams();
  const summary = props.jobs.find((job) => job.job_id === params.get("job")) ?? props.jobs[0];
  const detail = useQuery({ ...queries.printJob(summary?.job_id ?? ""), enabled: Boolean(summary) });
  if (!summary) return <StatusNote tone="empty" title="No print jobs" />;
  return (
    <div className={view.split}>
      <QueryGate query={detail} loading="Opening pages" errorTitle="The job pages failed">
        {(job) => <PageViewer pages={printPages(job.job_id, job.page_names, job.data_pages)} />}
      </QueryGate>
      <PrintRail key={summary.job_id} jobs={props.jobs} job={summary} pageCount={detail.data?.page_names.length || summary.pages} onJob={(jobId): void => setParams({ job: jobId })} />
    </div>
  );
}
