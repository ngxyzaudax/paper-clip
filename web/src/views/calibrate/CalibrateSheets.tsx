import type { ReactElement } from "react";
import type { CalibrateState } from "../../api/careTypes";
import { StatusNote } from "../../components/ui/StatusNote";
import { PageViewer } from "../../components/viewer/PageViewer";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import { calibratePages, patchOverlays } from "./calibratePages";

export function CalibrateSheets(props: { state: CalibrateState }): ReactElement {
  const pages = calibratePages(props.state);
  if (pages.length === 0) return <StatusNote tone="empty" title="No sheet yet" detail="Render a sheet to see its patches." />;
  return (
    <section className={ui.card} aria-label="Calibration sheets and scans">
      <p className={ui.kicker}>Sheets and scans</p>
      <PageViewer pages={pages} overlays={patchOverlays(props.state)} pageWidth={props.state.sheet_px.w} pageHeight={props.state.sheet_px.h} />
      <p className={view.caption}>Green patches passed, red failed, dashed were not read yet.</p>
    </section>
  );
}
