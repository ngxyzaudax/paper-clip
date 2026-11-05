import type { ReactElement } from "react";
import { artifactUrl } from "../../api/client";
import type { Wizard } from "../../api/careTypes";
import { printPageLabel } from "../../components/viewer/artifactPages";
import { classes } from "../../lib/classes";
import view from "../../styles/view.module.css";
import { groupSheets, keptFor, pageSlots, slotCue } from "./board";
import { readinessCopy } from "./readiness";
import { scanIndexOf } from "./scanPages";

export function PageBoard(props: { wizard: Wizard; onView: (index: number) => void }): ReactElement {
  if (props.wizard.total_pages <= 0) return <WaitingSheet />;
  const copy = readinessCopy(props.wizard.readiness);
  const groups = groupSheets(pageSlots(props.wizard.total_pages, props.wizard.duplex));
  return (
    <div className={view.stack}>
      {groups.map((group) => (
        <section key={group.sheet} className={view.sheet}>
          <p className={view.sheetHead}>Sheet {group.sheet}</p>
          <div className={view.slots}>
            {group.slots.map((slot) => <Slot key={slot.pageIndex} wizard={props.wizard} pageIndex={slot.pageIndex} side={slot.side} sheet={slot.sheet} onView={props.onView} />)}
          </div>
        </section>
      ))}
      <p className={view.caption}>{copy.text}</p>
      {copy.warn ? <p className={view.warn}>{copy.warn}</p> : null}
    </div>
  );
}

function WaitingSheet(): ReactElement {
  return (
    <section className={view.sheet}>
      <p className={view.sheetHead}>Sheet</p>
      <article className={classes(view.slot, view.next)}>
        <strong>Any page</strong>
        <span>Face down on the glass</span>
      </article>
    </section>
  );
}

function Slot(props: { wizard: Wizard; pageIndex: number; side: string; sheet: number; onView: (index: number) => void }): ReactElement {
  const scan = keptFor(props.wizard.scans, props.pageIndex);
  const cue = slotCue(props.wizard.step, props);
  const label = printPageLabel(props.pageIndex, props.wizard.data_pages);
  return (
    <article className={classes(view.slot, props.side === "Front" && view.front, cue && !scan && view.next)}>
      <strong>{label}</strong>
      <span>{scan ? props.side : cueText(cue, props.wizard.step)}</span>
      {scan ? (
        <button type="button" className={view.slotImage} onClick={(): void => props.onView(scanIndexOf(props.wizard, scan.name))} aria-label={`View the scan of ${label}`}>
          <img src={artifactUrl("scan", props.wizard.job_id, scan.name, 320)} alt="" style={scan.rotation === 180 ? { transform: "rotate(180deg)" } : undefined} />
        </button>
      ) : null}
    </article>
  );
}

function cueText(cue: boolean, step: Wizard["step"]): string {
  if (!cue) return "Waiting";
  if (step.action === "flip") return "Flip this side onto the glass";
  if (step.side === "either") return "Either side, face down";
  return "Face down";
}
