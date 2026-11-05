import type { ReactElement } from "react";
import type { ScanStep } from "../../api/careTypes";
import view from "../../styles/view.module.css";

export function ScanGuide(props: { step: ScanStep }): ReactElement {
  const step = props.step;
  return (
    <section className={view.guide} aria-live="polite">
      <p className={view.sheetHead}>{stepTitle(step.action)}</p>
      <p className={view.prompt}>{step.text}</p>
      {step.total > 0 ? <Progress done={step.done} total={step.total} /> : null}
    </section>
  );
}

function stepTitle(action: ScanStep["action"]): string {
  if (action === "flip") return "Flip";
  if (action === "next") return "Next sheet";
  if (action === "done") return "Ready to decode";
  if (action === "retry") return "Try that side again";
  return "Start with any page";
}

function Progress(props: { done: number; total: number }): ReactElement {
  const width = `${Math.round((props.done / props.total) * 100)}%`;
  return (
    <div className={view.guide}>
      <p className={view.caption}>{props.done} of {props.total} sides</p>
      <div className={view.track} aria-hidden="true"><span style={{ width }} /></div>
    </div>
  );
}
