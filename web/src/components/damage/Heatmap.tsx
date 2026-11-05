import type { ReactElement } from "react";
import styles from "./damage.module.css";

export function Heatmap(props: { map: number[][]; label: string }): ReactElement | null {
  const columns = props.map[0]?.length ?? 0;
  if (columns === 0) return null;
  return (
    <div className={styles.heat} role="img" aria-label={`${props.label}: ${summary(props.map)}`} style={{ gridTemplateColumns: `repeat(${columns}, 18px)` }}>
      {props.map.flatMap((row, rowIndex) => row.map((value, column) => <span key={`${rowIndex}-${column}`} style={{ background: heatColor(value) }} title={`${percent(value)} misread`} />))}
    </div>
  );
}

function summary(map: number[][]): string {
  const cells = map.flat();
  const worst = Math.max(...cells);
  if (worst < 0.01) return "every area was misread by under 1%";
  const hit = cells.filter((value) => value > 0).length;
  return `${hit} of ${cells.length} areas misread, worst ${percent(worst)}`;
}

function percent(value: number): string {
  return value > 0 && value < 0.01 ? "under 1%" : `${Math.round(value * 100)}%`;
}

function heatColor(value: number): string {
  if (value <= 0) return "var(--line)";
  const mix = Math.round(Math.min(1, value / 0.12) * 70);
  return `color-mix(in srgb, var(--critical) ${mix}%, var(--line))`;
}
