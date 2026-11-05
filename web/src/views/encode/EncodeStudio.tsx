import { useMutation } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { sendJson } from "../../api/client";
import type { EncodeOptions, EncodePreview, PreviewRequest, TaskStart } from "../../api/types";
import { TaskProgress } from "../../components/ui/TaskProgress";
import { StatusNote } from "../../components/ui/StatusNote";
import { useTask } from "../../hooks/useTask";
import view from "../../styles/view.module.css";
import ui from "../../styles/ui.module.css";
import { EncodeDrop } from "./EncodeDrop";
import { EncodePlanCard } from "./EncodePlanCard";
import { EncodePreviewPane } from "./EncodePreviewPane";
import { EncodeResult } from "./EncodeResult";
import { EncodeSettings } from "./EncodeSettings";
import { encodeBody, previewRequest } from "./previewRequest";
import { useEncodeDraft } from "./useEncodeDraft";
import { useEncodePreview } from "./useEncodePreview";
import styles from "./encode.module.css";

export function EncodeStudio(props: { options: EncodeOptions }): ReactElement {
  const draft = useEncodeDraft(props.options);
  const request = previewRequest(draft);
  const preview = useEncodePreview(request);
  const task = useTask();
  const encode = useMutation({
    mutationFn: (): Promise<TaskStart> => postEncode(draft.fileId, preview.data, request),
    onSuccess: (started) => task.start(started.task_id),
  });
  const pages = preview.data?.plan.total_pages ?? 0;
  return (
    <div className={view.studio}>
      <EncodeDrop fileId={draft.fileId} onFile={draft.setFile} />
      <div className={styles.column}>
        <EncodePreviewPane preview={preview} fileLoaded={Boolean(draft.fileId)} page={draft.page} layers={draft.layers} onPage={draft.setPage} onToggle={draft.toggleLayer} />
        {preview.data ? <EncodePlanCard plan={preview.data.plan} /> : null}
        <div className={ui.row}>
          <button type="button" className={ui.primary} disabled={!draft.fileId || !preview.data || preview.isFetching || task.view.status === "running"} onClick={(): void => encode.mutate()}>
            {draft.fileId ? `Encode ${pages} ${pages === 1 ? "page" : "pages"}` : "Drop a file to encode"}
          </button>
        </div>
        {encode.isError ? <StatusNote tone="error" title="Encode did not start" detail={encode.error.message} /> : null}
        <TaskProgress view={task.view} />
        <EncodeResult view={task.view} sha={preview.data?.plan.sha256 ?? ""} />
      </div>
      <EncodeSettings options={props.options} draft={draft} />
    </div>
  );
}

function postEncode(fileId: string | null, preview: EncodePreview | undefined, request: PreviewRequest): Promise<TaskStart> {
  if (!fileId || !preview) return Promise.reject(new Error("Choose a file and wait for the preview."));
  return sendJson<TaskStart>("/api/encode", "POST", encodeBody(fileId, preview.preview_id, request));
}
