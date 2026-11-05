import type { ReactElement } from "react";
import ui from "../../styles/ui.module.css";

export function FactList(props: { rows: { label: string; value: string }[] }): ReactElement {
  return (
    <dl className={ui.facts}>
      {props.rows.map((row) => (
        <div className={ui.fact} key={row.label}>
          <dt>{row.label}</dt>
          <dd>{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}
