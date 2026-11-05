import { useQueryClient } from "@tanstack/react-query";
import type { ChangeEvent, ReactElement } from "react";
import { getJson } from "../../api/client";
import type { EncodeField, EncodeOptions } from "../../api/types";
import { Reveal } from "../../components/ui/Reveal";
import { useViewMode } from "../../components/shell/ViewModeContext";
import { classes } from "../../lib/classes";
import type { ViewMode } from "../../lib/viewMode";
import ui from "../../styles/ui.module.css";
import layout from "../../styles/view.module.css";
import mode from "../../components/shell/mode.module.css";
import type { EncodeDraft } from "./useEncodeDraft";
import { hiddenEdits, setupTitle, visibleFields } from "./previewRequest";
import { SettingField } from "./SettingField";
import styles from "./encode.module.css";

const GROUPS: { level: ViewMode; title: string }[] = [
  { level: "simple", title: "Sheet" },
  { level: "advanced", title: "Protection" },
  { level: "expert", title: "Dots and markers" },
];
const NEEDS_FILL = new Set(["sheets", "fill_priority"]);

export function EncodeSettings(props: { options: EncodeOptions; draft: EncodeDraft }): ReactElement {
  const client = useQueryClient();
  const view = useViewMode().mode;
  const fields = visibleFields(props.options, view);
  const hidden = hiddenEdits(props.options, props.draft.picks, props.draft.margin, view);
  const reset = (): void => void reload(client, props.draft.applyDefaults);
  return (
    <div className={styles.column}>
      <section className={classes(ui.card, styles.column)} aria-label="Encoding settings">
        <p className={ui.kicker}>{setupTitle(props.options, props.draft.picks, props.draft.margin)}</p>
        {GROUPS.map((group) => (
          <FieldGroup key={group.level} title={group.title} fields={fields.filter((field) => field.level === group.level)} draft={props.draft} />
        ))}
        <Reveal at="advanced">
          <label className={ui.field}>
            <span>Blank edge (millimetres)</span>
            <input className={ui.input} type="number" min={0} step="0.5" value={props.draft.margin} onChange={(event): void => changeMargin(event, props.draft.setMargin)} />
            <p className={layout.caption}>Blank paper around the dots, so the printer does not cut them off.</p>
          </label>
        </Reveal>
        <label className={ui.field}>
          <span>Passphrase (optional)</span>
          <input className={ui.input} type="password" value={props.draft.passphrase} autoComplete="off" onChange={(event): void => props.draft.setPassphrase(event.target.value)} />
          <p className={layout.caption}>Leave this empty unless you want a phrase that is required to read the pages back.</p>
        </label>
        {hidden.length > 0 ? (
          <p className={mode.hidden}>
            <span>{hiddenNote(hidden)}</span>
            <button type="button" className={ui.quiet} onClick={reset}>Reset</button>
          </p>
        ) : null}
        <button type="button" className={ui.quiet} onClick={reset}>Reset to saved setup</button>
      </section>
    </div>
  );
}

function FieldGroup(props: { title: string; fields: EncodeField[]; draft: EncodeDraft }): ReactElement | null {
  if (props.fields.length === 0) return null;
  const filling = props.draft.picks.fill_sheets === true;
  return (
    <fieldset className={styles.group}>
      <legend>{props.title}</legend>
      {props.fields.some((field) => NEEDS_FILL.has(field.key)) && props.draft.picks.fill_sheets !== true ? <p className={layout.caption}>Turn on Fill the sheets to use these.</p> : null}
      {props.fields.map((field) => (
        <SettingField key={field.key} field={field} value={props.draft.picks[field.key]} disabled={NEEDS_FILL.has(field.key) && !filling} onChange={props.draft.setPick} />
      ))}
    </fieldset>
  );
}

function hiddenNote(hidden: string[]): string {
  const verb = hidden.length === 1 ? "is hidden in this view and differs" : "are hidden in this view and differ";
  return `${hidden.length} ${hidden.length === 1 ? "setting" : "settings"} ${verb} from the saved setup: ${hidden.join(", ")}`;
}

function changeMargin(event: ChangeEvent<HTMLInputElement>, setMargin: (margin: number) => void): void {
  const value = Number(event.target.value);
  if (Number.isFinite(value)) setMargin(value);
}

async function reload(client: ReturnType<typeof useQueryClient>, apply: (options: EncodeOptions) => void): Promise<void> {
  const fresh = await client.fetchQuery({ queryKey: ["encode-options"], queryFn: (): Promise<EncodeOptions> => getJson<EncodeOptions>("/api/encode/options") });
  apply(fresh);
}
