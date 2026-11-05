import { useEffect, useState } from "react";
import type { CSSProperties, ReactElement, SyntheticEvent } from "react";
import { Loupe } from "./Loupe";
import { PageOverlay } from "./PageOverlay";
import type { OverlayLayer, ViewerPage } from "./types";
import type { ViewerState } from "./useViewerState";
import styles from "./viewer.module.css";

type Size = { w: number; h: number };

export function PageStage(props: {
  base: ViewerPage;
  cover: ViewerPage | null;
  state: ViewerState;
  overlays: OverlayLayer[];
  pageWidth?: number;
  pageHeight?: number;
}): ReactElement {
  const [natural, setNatural] = useState<Size>({ w: 0, h: 0 });
  useEffect(() => setNatural({ w: 0, h: 0 }), [props.base.src]);
  const source = props.state.zoom > 1.4 && props.base.hires ? props.base.hires : props.base.src;
  const turn = props.state.upright ? (props.base.rotation ?? 0) % 360 : 0;
  return (
    <div className={styles.stage}>
      <div className={styles.frame} style={frameStyle(props.state.zoom, turn, natural)}>
        <img className={styles.base} src={source} alt={props.base.label} onLoad={rememberSize(setNatural)} />
        {props.cover && props.state.split > 0 ? (
          <img className={styles.cover} src={props.cover.src} alt={props.cover.label} style={{ clipPath: `inset(0 ${100 - props.state.split}% 0 0)` }} />
        ) : null}
        <PageOverlay layers={props.overlays} width={props.pageWidth ?? natural.w} height={props.pageHeight ?? natural.h} />
        {props.state.loupe && props.base.crop ? <Loupe crop={props.base.crop} turn={turn} /> : null}
      </div>
    </div>
  );
}

const FIT_HEIGHT_VH = 66;

function frameStyle(zoom: number, turn: number, natural: Size): CSSProperties {
  return { width: frameWidth(zoom, natural), transform: turn ? `rotate(${turn}deg)` : undefined };
}

function frameWidth(zoom: number, natural: Size): string {
  if (natural.h <= 0) return `${zoom * 100}%`;
  const fitted = `${(FIT_HEIGHT_VH * natural.w) / natural.h}vh`;
  return `calc(min(100%, ${fitted}) * ${zoom})`;
}

function rememberSize(setNatural: (size: Size) => void): (event: SyntheticEvent<HTMLImageElement>) => void {
  return (event: SyntheticEvent<HTMLImageElement>): void => {
    setNatural({ w: event.currentTarget.naturalWidth, h: event.currentTarget.naturalHeight });
  };
}
