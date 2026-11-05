import * as Select from "@radix-ui/react-select";
import type { ReactElement } from "react";
import controls from "../../styles/controls.module.css";
import ui from "../../styles/ui.module.css";

export function SelectField(props: {
  label: string;
  value: string;
  onValueChange: (value: string) => void;
  options: { label: string; value: string }[];
  disabled?: boolean;
}): ReactElement {
  const options = props.options.filter((option) => option.value !== "");
  const known = options.some((option) => option.value === props.value);
  return (
    <label className={ui.field}>
      <span>{props.label}</span>
      <Select.Root value={known ? props.value : undefined} onValueChange={props.onValueChange} disabled={props.disabled}>
        <Select.Trigger className={ui.trigger} aria-label={props.label}>
          <Select.Value placeholder="Choose" />
        </Select.Trigger>
        <Select.Portal>
          <Select.Content className={controls.menu} position="popper">
            <Select.Viewport>
              {options.map((option) => (
                <Select.Item key={`${option.value}-${option.label}`} value={option.value} className={controls.item}>
                  <Select.ItemText>{option.label}</Select.ItemText>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>
    </label>
  );
}
