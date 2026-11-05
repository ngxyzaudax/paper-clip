import type { ReactElement } from "react";
import { StatusNote } from "../ui/StatusNote";
import { PageFilmstrip } from "./PageFilmstrip";
import { PageStage } from "./PageStage";
import { PageToolbar } from "./PageToolbar";
import type { OverlayLayer, PageViewerProps } from "./types";
import { useViewerState } from "./useViewerState";
import { nextZoom } from "./zoom";
import styles from "./viewer.module.css";

export function PageViewer(props: PageViewerProps): ReactElement {
  const state = useViewerState(props.pages, props.index, props.onIndex);
  const base = props.pages[state.index];
  if (!base) return <StatusNote tone="empty" title={props.empty ?? "No page image"} />;
  const cover = props.pages[state.index + 1] ?? null;
  return (
    <div className={styles.viewer}>
      <PageToolbar
        page={base}
        position={`${state.index + 1} / ${props.pages.length}`}
        state={state}
        canCompare={cover !== null}
        onZoom={(direction): void => state.setZoom(nextZoom(state.zoom, direction))}
      />
      <PageStage
        base={base}
        cover={cover}
        state={state}
        overlays={overlaysFor(props.overlays, state.index)}
        pageWidth={props.pageWidth}
        pageHeight={props.pageHeight}
      />
      <PageFilmstrip pages={props.pages} index={state.index} onSelect={state.select} />
    </div>
  );
}

function overlaysFor(overlays: PageViewerProps["overlays"], index: number): OverlayLayer[] {
  if (!overlays) return [];
  return typeof overlays === "function" ? overlays(index) : overlays;
}
