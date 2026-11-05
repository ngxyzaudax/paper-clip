import type { ReactElement } from "react";
import type { Wizard } from "../../api/careTypes";
import { PageViewer } from "../../components/viewer/PageViewer";
import ui from "../../styles/ui.module.css";
import { scanPages } from "./scanPages";

export function ScanViewer(props: { wizard: Wizard; index: number; onIndex: (index: number) => void }): ReactElement | null {
  if (props.wizard.scans.length === 0) return null;
  return (
    <section className={ui.card} aria-label="Raw scans">
      <p className={ui.kicker}>Raw scans · {props.wizard.scans.length}</p>
      <PageViewer pages={scanPages(props.wizard)} index={props.index} onIndex={props.onIndex} />
    </section>
  );
}
