import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { getJson } from "../../api/client";
import type { FileMeta } from "../../api/types";
import { QueryGate } from "../ui/QueryGate";
import { FileViewer } from "./FileViewer";

export function decodedUrl(jobId: string, name: string): string {
  return `/api/files/decoded/${encodeURIComponent(jobId)}/${encodeURIComponent(name)}`;
}

export function DecodedFile(props: { jobId: string; name: string }): ReactElement {
  const src = decodedUrl(props.jobId, props.name);
  const meta = useQuery({
    queryKey: ["decoded-file", props.jobId, props.name],
    queryFn: (): Promise<FileMeta> => getJson<FileMeta>(`${src}/meta`),
  });
  return (
    <QueryGate query={meta} loading="Opening the recovered file" errorTitle="Could not open the recovered file">
      {(file) => <FileViewer meta={file} src={src} />}
    </QueryGate>
  );
}
