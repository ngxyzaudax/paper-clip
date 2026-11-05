import { useState } from "react";
import type { ReactElement } from "react";
import type { LibraryDetail } from "../../api/careTypes";
import { StatusNote } from "../../components/ui/StatusNote";
import { DecodedFile } from "../../components/viewer/DecodedFile";
import { PageViewer } from "../../components/viewer/PageViewer";
import { classes } from "../../lib/classes";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import { libraryRecords } from "./recordList";
import type { LibraryRecord } from "./recordList";

export function LibraryRecords(props: { detail: LibraryDetail }): ReactElement {
  const records = libraryRecords(props.detail);
  const [chosenKey, setChosenKey] = useState(records[0]?.key ?? "");
  const chosen = records.find((record) => record.key === chosenKey) ?? records[0];
  if (!chosen) return <StatusNote tone="empty" title="No sheets, scans, or recovered copies yet" />;
  return (
    <div className={view.stack}>
      <div className={ui.row} role="group" aria-label="Records of this file">
        {records.map((record) => (
          <button key={record.key} type="button" className={classes(ui.quiet, record.key === chosen.key && view.viewed)} aria-pressed={record.key === chosen.key} title={record.detail} onClick={(): void => setChosenKey(record.key)}>
            {record.label}
          </button>
        ))}
      </div>
      <p className={view.caption}>{chosen.detail}</p>
      <RecordBody record={chosen} />
    </div>
  );
}

function RecordBody(props: { record: LibraryRecord }): ReactElement {
  if (props.record.recovered) return <DecodedFile jobId={props.record.recovered.jobId} name={props.record.recovered.name} />;
  return <PageViewer pages={props.record.pages} empty="This record holds no images" />;
}
