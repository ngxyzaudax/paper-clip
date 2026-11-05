import type { LibraryDetail } from "../../api/careTypes";
import { counted, formatWhen } from "../../lib/format";

export function timelineLines(detail: LibraryDetail): string[] {
  return [
    ...detail.prints.map((job) => `Printed ${formatWhen(job.created)} · ${counted(job.pages, "page")}`),
    ...detail.scans.map((job) => `Scanned ${formatWhen(job.created)} · ${counted(job.pages, "page")}`),
    ...detail.recovered.map((file) => `Recovered ${file.name}`),
    ...detail.readings.map((reading) => `Checked ${formatWhen(reading.time)} · ${careWords(reading.status)}`),
  ];
}

function careWords(status: string): string {
  if (status === "Worn") return "Worn, still readable";
  if (status === "Healthy") return "Readable";
  return status;
}
