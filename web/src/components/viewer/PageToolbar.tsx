import { ExternalLink, RotateCw, Search, ZoomIn, ZoomOut } from "lucide-react";
import type { ReactElement } from "react";
import { classes } from "../../lib/classes";
import ui from "../../styles/ui.module.css";
import { Reveal } from "../ui/Reveal";
import type { ViewerPage } from "./types";
import type { ViewerState } from "./useViewerState";
import { zoomLabel } from "./zoom";
import styles from "./viewer.module.css";

export function PageToolbar(props: {
  page: ViewerPage;
  position: string;
  state: ViewerState;
  canCompare: boolean;
  onZoom: (direction: 1 | -1) => void;
}): ReactElement {
  const turned = (props.page.rotation ?? 0) % 360 !== 0;
  return (
    <div className={styles.toolbar}>
      <button type="button" className={ui.quiet} onClick={(): void => props.onZoom(-1)} aria-label="Zoom out"><ZoomOut size={16} /></button>
      <span className={styles.mono}>{zoomLabel(props.state.zoom)}</span>
      <button type="button" className={ui.quiet} onClick={(): void => props.onZoom(1)} aria-label="Zoom in"><ZoomIn size={16} /></button>
      {props.page.crop ? (
        <button type="button" className={classes(ui.quiet, props.state.loupe && styles.on)} aria-pressed={props.state.loupe} onClick={props.state.toggleLoupe}>
          <Search size={15} /> Loupe
        </button>
      ) : null}
      {turned ? (
        <button type="button" className={classes(ui.quiet, props.state.upright && styles.on)} aria-pressed={props.state.upright} onClick={props.state.toggleUpright}>
          <RotateCw size={15} /> {props.state.upright ? "Upright" : "As scanned"}
        </button>
      ) : null}
      <span className={styles.title}>{props.page.label}{props.page.note ? ` · ${props.page.note}` : ""}</span>
      <span className={styles.mono}>{props.position}</span>
      <Reveal at="advanced">
        {props.canCompare ? (
          <input className={styles.slider} type="range" min={0} max={100} value={props.state.split} aria-label="Compare with the next page" onChange={(event): void => props.state.setSplit(Number(event.target.value))} />
        ) : null}
      </Reveal>
      {props.page.original ? (
        <a className={ui.quiet} href={props.page.original} target="_blank" rel="noreferrer"><ExternalLink size={15} /> Original</a>
      ) : null}
    </div>
  );
}
