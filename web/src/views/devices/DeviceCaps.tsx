import type { ReactElement } from "react";
import { StatusNote } from "../../components/ui/StatusNote";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import { capError, capSummary } from "./caps";

export type CapsQuery = { isFetching: boolean; isError: boolean; error: Error | null; data?: Record<string, unknown>; refetch: () => Promise<unknown> };

export function DeviceCaps(props: { title: string; chosen: boolean; query: CapsQuery }): ReactElement {
  const failed = props.query.isError ? props.query.error?.message ?? "" : capError(props.query.data);
  const summary = capSummary(props.query.data);
  return (
    <section className={ui.card}>
      <p className={ui.kicker}>{props.title}</p>
      {props.chosen ? null : <p className={view.caption}>Choose a {props.title.toLowerCase()} to see what it can do.</p>}
      {props.query.isFetching && !failed ? <StatusNote tone="busy" title="Checking the device" /> : null}
      {failed ? <StatusNote tone="error" title={`Could not check the ${props.title.toLowerCase()}`} detail={failed} onRetry={(): void => void props.query.refetch()} /> : null}
      {summary ? <p className={view.caption}>{summary}</p> : null}
    </section>
  );
}
