import type { LibraryDetail } from "../../api/careTypes";
import { artifactPage, printPages } from "../../components/viewer/artifactPages";
import type { ViewerPage } from "../../components/viewer/types";
import { counted, formatWhen } from "../../lib/format";

export type LibraryRecord = { key: string; label: string; detail: string; pages: ViewerPage[]; recovered?: { jobId: string; name: string } };

export function libraryRecords(detail: LibraryDetail): LibraryRecord[] {
  return [...printRecords(detail), ...scanRecords(detail), ...recoveredRecords(detail)];
}

function printRecords(detail: LibraryDetail): LibraryRecord[] {
  return detail.prints.map((job) => ({
    key: `print-${job.job_id}`,
    label: `Sheets · ${formatWhen(job.created)}`,
    detail: `${counted(job.pages, "page")} · ${job.sides === 2 ? "both sides" : "one side"}${job.paper_size ? ` · ${job.paper_size}` : ""}`,
    pages: printPages(job.job_id, job.page_names, job.data_pages),
  }));
}

function scanRecords(detail: LibraryDetail): LibraryRecord[] {
  return detail.scans.map((job) => ({
    key: `scan-${job.job_id}`,
    label: `Scans · ${formatWhen(job.created)}`,
    detail: counted(job.pages, "raw scan"),
    pages: job.names.map((name, index) => artifactPage("scan", job.job_id, name, `Scan ${index + 1}`)),
  }));
}

function recoveredRecords(detail: LibraryDetail): LibraryRecord[] {
  return detail.recovered.map((file) => ({
    key: `recovered-${file.job_id}-${file.name}`,
    label: `Recovered · ${file.name}`,
    detail: "Read back from the scans",
    pages: [],
    recovered: { jobId: file.job_id, name: file.name },
  }));
}
