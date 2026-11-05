import type { ReactElement } from "react";
import type { EncodeField, PickValue } from "../../api/types";
import { SelectField } from "../../components/ui/SelectField";
import { SwitchField } from "../../components/ui/SwitchField";
import styles from "./encode.module.css";

export function SettingField(props: {
  field: EncodeField;
  value: PickValue | undefined;
  disabled?: boolean;
  onChange: (key: string, value: string | boolean) => void;
}): ReactElement {
  return (
    <div className={styles.setting} data-disabled={props.disabled ? "true" : undefined}>
      {props.field.kind === "switch" ? (
        <SwitchField label={props.field.label} checked={props.value === true} onCheckedChange={(checked): void => props.onChange(props.field.key, checked)} />
      ) : (
        <SelectField
          label={props.field.label}
          value={String(props.value ?? "")}
          disabled={props.disabled}
          options={props.field.options.map((option) => ({ label: option.label, value: String(option.value) }))}
          onValueChange={(value): void => props.onChange(props.field.key, value)}
        />
      )}
      {props.field.hint ? <p className={styles.hint}>{props.field.hint}</p> : null}
    </div>
  );
}
