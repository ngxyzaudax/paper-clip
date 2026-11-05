import type { ReactElement } from "react";
import type { CalibrateState } from "../../api/careTypes";
import { Reveal } from "../../components/ui/Reveal";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";

export function CalibrateReport(props: { state: CalibrateState }): ReactElement {
  return (
    <div className={view.stack}>
      <section className={ui.card}>
        <p className={ui.kicker}>Next · {props.state.next_step}</p>
        <p>{props.state.sheet_ready ? "The sheet is ready to print." : "Render a sheet before printing."}</p>
        <ol>
          {props.state.steps.map((step) => <li key={step.label}>{step.done ? "Done" : "Open"} · {step.label}</li>)}
        </ol>
      </section>
      <Reveal at="expert">
        {props.state.axes.map((axis) => (
          <section key={axis.name} className={ui.card}>
            <h2>{axis.name}</h2>
            <p>Passed {axis.passed.join(", ") || "—"}</p>
            <p>Failed {axis.failed.join(", ") || "—"}</p>
            <p>Chosen {axis.chosen || "—"}</p>
          </section>
        ))}
      </Reveal>
      {props.state.profile_rows ? (
        <table className={view.table}>
          <caption className={view.caption}>Profile change if you save now</caption>
          <thead><tr><th scope="col">Setting</th><th scope="col">Now</th><th scope="col">After</th></tr></thead>
          <tbody>
            {props.state.profile_rows.map((row) => <tr key={row.label}><th scope="row">{row.label}</th><td>{row.now}</td><td>{row.after}</td></tr>)}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
