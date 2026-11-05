import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import type { ReactElement } from "react";
import { sendJson } from "../../api/client";
import type { ScanItem, Wizard } from "../../api/careTypes";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { StatusNote } from "../../components/ui/StatusNote";
import { useShows } from "../../components/shell/ViewModeContext";
import { classes } from "../../lib/classes";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import { scanLabel, scanNote } from "./scanPages";

type RowActions = { onView: (index: number) => void; onKeep: (name: string) => void; onRemove: (name: string) => void };

export function ScanRows(props: { wizard: Wizard; viewed: string; onView: (index: number) => void; onChanged: () => void }): ReactElement | null {
  const [pending, setPending] = useState<string | null>(null);
  const scanPath = (name: string): string => `/api/decode/sessions/${encodeURIComponent(props.wizard.job_id)}/scans/${encodeURIComponent(name)}`;
  const remove = useMutation({ mutationFn: (name: string): Promise<unknown> => sendJson(scanPath(name), "DELETE"), onSuccess: props.onChanged });
  const keep = useMutation({ mutationFn: (name: string): Promise<unknown> => sendJson(`${scanPath(name)}/keep`, "POST"), onSuccess: props.onChanged });
  if (props.wizard.scans.length === 0) return null;
  const actions: RowActions = { onView: props.onView, onKeep: keep.mutate, onRemove: setPending };
  return (
    <div className={view.list} aria-label="Scans in this session">
      {props.wizard.scans.map((scan, index) => <ScanRow key={scan.name} scan={scan} index={index} dataPages={props.wizard.data_pages} viewed={scan.name === props.viewed} actions={actions} />)}
      {remove.isError ? <StatusNote tone="error" title="Could not remove the scan" detail={remove.error.message} /> : null}
      {keep.isError ? <StatusNote tone="error" title="Could not keep the scan" detail={keep.error.message} /> : null}
      <ConfirmDialog open={pending !== null} title="Remove this scan" body="Delete this scan and scan that side again." confirmLabel="Remove" onOpenChange={(open): void => { if (!open) setPending(null); }} onConfirm={(): void => { if (pending) remove.mutate(pending); setPending(null); }} />
    </div>
  );
}

function ScanRow(props: { scan: ScanItem; index: number; dataPages: number; viewed: boolean; actions: RowActions }): ReactElement {
  const detailed = useShows("advanced");
  return (
    <article className={classes(ui.card, props.viewed && view.viewed)}>
      <strong>{scanLabel(props.scan, props.dataPages)}</strong>
      <p>{rowDetail(props.scan, detailed)}</p>
      {props.scan.status === "unidentified" ? <p>Face down, lid closed, not a mirror copy.</p> : null}
      <div className={ui.row}>
        <button type="button" className={ui.quiet} aria-pressed={props.viewed} onClick={(): void => props.actions.onView(props.index)}>View</button>
        {props.scan.status === "duplicate" ? <button type="button" className={ui.quiet} onClick={(): void => props.actions.onKeep(props.scan.name)}>Keep</button> : null}
        <button type="button" className={ui.quiet} onClick={(): void => props.actions.onRemove(props.scan.name)}>Remove</button>
      </div>
    </article>
  );
}

function rowDetail(scan: ScanItem, detailed: boolean): string {
  if (!detailed) return scanNote(scan);
  const extra = [scan.rotation ? `turned ${scan.rotation}°` : ""].filter(Boolean);
  return [scanNote(scan), ...extra].join(" · ");
}
