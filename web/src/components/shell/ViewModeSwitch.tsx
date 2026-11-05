import * as Tooltip from "@radix-ui/react-tooltip";
import type { KeyboardEvent, ReactElement } from "react";
import { classes } from "../../lib/classes";
import { VIEW_MODES } from "../../lib/viewMode";
import type { ViewMode } from "../../lib/viewMode";
import { useViewMode } from "./ViewModeContext";
import styles from "./mode.module.css";

export function ViewModeSwitch(): ReactElement {
  const { mode, setMode } = useViewMode();
  return (
    <div className={styles.modes} role="radiogroup" aria-label="View mode" onKeyDown={(event): void => step(event, mode, setMode)}>
      {VIEW_MODES.map((item) => (
        <Tooltip.Root key={item.mode}>
          <Tooltip.Trigger asChild>
            <button
              type="button"
              role="radio"
              aria-checked={item.mode === mode}
              tabIndex={item.mode === mode ? 0 : -1}
              className={classes(styles.mode, item.mode === mode && styles.chosen)}
              onClick={(): void => setMode(item.mode)}
            >
              {item.label}
            </button>
          </Tooltip.Trigger>
          <Tooltip.Portal>
            <Tooltip.Content className={styles.tip} sideOffset={8}>{item.detail}</Tooltip.Content>
          </Tooltip.Portal>
        </Tooltip.Root>
      ))}
    </div>
  );
}

function step(event: KeyboardEvent<HTMLDivElement>, mode: ViewMode, setMode: (mode: ViewMode) => void): void {
  const offset = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
  if (offset === 0) return;
  event.preventDefault();
  const index = VIEW_MODES.findIndex((item) => item.mode === mode);
  const next = VIEW_MODES[(index + offset + VIEW_MODES.length) % VIEW_MODES.length];
  if (!next) return;
  setMode(next.mode);
  const buttons = event.currentTarget.querySelectorAll<HTMLButtonElement>("button");
  buttons[VIEW_MODES.indexOf(next)]?.focus();
}
