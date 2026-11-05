import type { ReactElement, ReactNode } from "react";
import ui from "../../styles/ui.module.css";

export function PageHeader(props: { kicker: string; title: string; lede?: string; children?: ReactNode }): ReactElement {
  return (
    <header className={ui.header}>
      <div>
        <p className={ui.kicker}>{props.kicker}</p>
        <h1>{props.title}</h1>
        {props.lede ? <p className={ui.lede}>{props.lede}</p> : null}
      </div>
      {props.children ? <div className={ui.actions}>{props.children}</div> : null}
    </header>
  );
}
