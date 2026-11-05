import type { QueryClient } from "@tanstack/react-query";
import { getJson } from "./client";
import type { ArchiveIndex, CalibrateState, HealthDetail, HealthRow, LibraryDetail, LibraryIndex } from "./careTypes";
import type { HomePayload, PrintJobDetail, PrintJobSummary, ScanSummary } from "./types";

type QueryDef<T> = { queryKey: readonly unknown[]; queryFn: () => Promise<T> };

const STABLE_KEYS = new Set(["encode-preview", "encode-options", "inbox-meta", "printer-caps", "scanner-caps", "decoded-file"]);

function query<T>(key: readonly unknown[], path: string): QueryDef<T> {
  return { queryKey: key, queryFn: (): Promise<T> => getJson<T>(path) };
}

export const queries = {
  home: (): QueryDef<HomePayload> => query(["home"], "/api/home"),
  library: (): QueryDef<LibraryIndex> => query(["library"], "/api/library"),
  libraryDoc: (sha: string): QueryDef<LibraryDetail> => query(["library", sha], `/api/library/${encodeURIComponent(sha)}`),
  archive: (): QueryDef<ArchiveIndex> => query(["archive"], "/api/archive"),
  printJobs: (): QueryDef<PrintJobSummary[]> => query(["print-jobs"], "/api/print/jobs"),
  printJob: (jobId: string): QueryDef<PrintJobDetail> => query(["print-job", jobId], `/api/print/jobs/${encodeURIComponent(jobId)}`),
  sessions: (): QueryDef<ScanSummary[]> => query(["decode-sessions"], "/api/decode/sessions"),
  health: (): QueryDef<HealthRow[]> => query(["health"], "/api/health"),
  healthDoc: (sha: string): QueryDef<HealthDetail> => query(["health", sha], `/api/health/${encodeURIComponent(sha)}`),
  calibrate: (): QueryDef<CalibrateState> => query(["calibrate"], "/api/calibrate"),
};

export function refreshAfterTask(client: QueryClient): Promise<void> {
  return client.invalidateQueries({ predicate: (item) => !STABLE_KEYS.has(String(item.queryKey[0])) });
}
