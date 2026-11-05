import { useState } from "react";
import type { ReactElement } from "react";
import type { OverlayLayer } from "./types";
import styles from "./viewer.module.css";

export function PageOverlay(props: { layers: OverlayLayer[]; width: number; height: number }): ReactElement | null {
  const [label, setLabel] = useState("");
  if (props.width <= 0 || props.height <= 0) return null;
  const rects = props.layers.flatMap((layer) => layer.rects.map((rect) => ({ ...rect, layer: layer.name })));
  return (
    <div className={styles.overlay}>
      <svg viewBox={`0 0 ${props.width} ${props.height}`} preserveAspectRatio="none">
        {rects.map((rect, index) => (
          <rect
            key={`${rect.layer}-${index}`}
            x={rect.x}
            y={rect.y}
            width={rect.w}
            height={rect.h}
            className={styles[rect.tone ?? rect.layer] ?? styles.rect}
            onMouseEnter={(): void => setLabel(rect.label ?? "")}
            onMouseLeave={(): void => setLabel("")}
          >
            {rect.label ? <title>{rect.label}</title> : null}
          </rect>
        ))}
      </svg>
      {label ? <span className={styles.hoverLabel}>{label}</span> : null}
    </div>
  );
}
