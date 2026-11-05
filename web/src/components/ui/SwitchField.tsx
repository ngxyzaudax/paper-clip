import * as Switch from "@radix-ui/react-switch";
import type { ReactElement } from "react";
import controls from "../../styles/controls.module.css";

export function SwitchField(props: { label: string; checked: boolean; onCheckedChange: (checked: boolean) => void }): ReactElement {
  return (
    <label className={controls.switchRow}>
      <span>{props.label}</span>
      <Switch.Root className={controls.switch} checked={props.checked} onCheckedChange={props.onCheckedChange} aria-label={props.label}>
        <Switch.Thumb className={controls.thumb} />
      </Switch.Root>
    </label>
  );
}
