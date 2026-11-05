import type { ReactElement } from "react";
import view from "../../styles/view.module.css";
import { chartPoints, yFor } from "./chartMath";

export function HealthChart(props: { values: number[] }): ReactElement | null {
  if (props.values.length === 0) return null;
  const width = 420;
  const height = 120;
  const only = props.values[0] ?? 0;
  return (
    <figure>
      <svg className={view.chart} viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Health over time">
        <line className={view.reprint} x1={8} x2={width - 8} y1={yFor(35, height)} y2={yFor(35, height)} />
        <polyline className={view.chartLine} points={chartPoints(props.values, width, height)} />
        {props.values.length === 1 ? <circle cx={width / 2} cy={yFor(only, height)} r={3} fill="var(--accent)" /> : null}
      </svg>
      <figcaption className={view.caption}>Reprint line at 35%.</figcaption>
    </figure>
  );
}
