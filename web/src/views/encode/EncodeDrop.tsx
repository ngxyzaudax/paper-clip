import { useMutation, useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { getJson, sendForm } from "../../api/client";
import type { FileMeta, InboxFile } from "../../api/types";
import { FileViewer } from "../../components/viewer/FileViewer";
import { QueryGate } from "../../components/ui/QueryGate";
import { StatusNote } from "../../components/ui/StatusNote";
import { useFileDrop } from "../../hooks/useFileDrop";
import { classes } from "../../lib/classes";
import styles from "./encode.module.css";

export function EncodeDrop(props: { fileId: string | null; onFile: (fileId: string) => void }): ReactElement {
  const upload = useMutation({ mutationFn: postInbox, onSuccess: (inbox) => props.onFile(inbox.file_id) });
  const drop = useFileDrop((files): void => upload.mutate(files[0]));
  return (
    <div className={styles.column}>
      <label className={classes(styles.drop, drop.hot && styles.hot)} {...drop.zone}>
        <input className={styles.file} type="file" onChange={drop.onInput} />
        <strong>{props.fileId ? "Drop another file" : "Drop a file"}</strong>
        <span>or choose one from this machine</span>
      </label>
      {upload.isPending ? <StatusNote tone="busy" title="Taking the file in" /> : null}
      {upload.isError ? <StatusNote tone="error" title="The inbox refused the file" detail={upload.error.message} /> : null}
      <InboxMeta fileId={props.fileId} />
    </div>
  );
}

function InboxMeta(props: { fileId: string | null }): ReactElement | null {
  const meta = useQuery({
    queryKey: ["inbox-meta", props.fileId],
    queryFn: (): Promise<FileMeta> => getJson<FileMeta>(`/api/files/inbox/${props.fileId ?? ""}/meta`),
    enabled: Boolean(props.fileId),
  });
  if (!props.fileId) return null;
  return (
    <QueryGate query={meta} loading="Reading the file" errorTitle="Could not read the file">
      {(file) => <FileViewer meta={file} src={`/api/files/inbox/${props.fileId}`} />}
    </QueryGate>
  );
}

function postInbox(file: File): Promise<InboxFile> {
  const body = new FormData();
  body.set("file", file);
  return sendForm<InboxFile>("/api/inbox", body);
}
