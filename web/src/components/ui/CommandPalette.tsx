import * as Dialog from "@radix-ui/react-dialog";
import { useEffect, useState } from "react";
import type { KeyboardEvent, ReactElement } from "react";
import { useNavigate } from "react-router-dom";
import { VIEW_MODES } from "../../lib/viewMode";
import type { ViewMode } from "../../lib/viewMode";
import { visibleNav } from "../shell/nav";
import { useViewMode } from "../shell/ViewModeContext";
import styles from "./dialog.module.css";

type Command = { id: string; label: string; detail: string; run: () => void };

export function CommandPalette(props: { open: boolean; onOpenChange: (open: boolean) => void }): ReactElement {
  const navigate = useNavigate();
  const { mode, setMode } = useViewMode();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  useEffect(() => {
    if (!props.open) return;
    setQuery("");
    setActive(0);
  }, [props.open]);
  const close = (): void => props.onOpenChange(false);
  const matches = commands(mode, (to) => { navigate(to); close(); }, (next) => { setMode(next); close(); })
    .filter((item) => `${item.label} ${item.detail}`.toLowerCase().includes(query.trim().toLowerCase()));
  const current = matches.length === 0 ? 0 : Math.min(active, matches.length - 1);
  function onKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
    const move = event.key === "ArrowDown" ? 1 : event.key === "ArrowUp" ? -1 : 0;
    if (move !== 0) {
      event.preventDefault();
      setActive(Math.min(Math.max(current + move, 0), Math.max(matches.length - 1, 0)));
    }
    if (event.key === "Enter" && matches[current]) {
      event.preventDefault();
      matches[current].run();
    }
  }
  return (
    <Dialog.Root open={props.open} onOpenChange={props.onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className={styles.overlay} />
        <Dialog.Content className={styles.palette} aria-describedby={undefined}>
          <Dialog.Title className={styles.filter} asChild>
            <input
              value={query}
              onChange={(event): void => setQuery(event.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Go to a desk or switch view"
              aria-label="Filter commands"
              role="combobox"
              aria-expanded="true"
              aria-controls="palette-list"
              aria-activedescendant={matches[current] ? `palette-${matches[current].id}` : undefined}
            />
          </Dialog.Title>
          {matches.length === 0 ? <p className={styles.empty}>No matching command</p> : (
            <div className={styles.list} role="listbox" id="palette-list" aria-label="Commands">
              {matches.map((item, index) => (
                <div key={item.id} id={`palette-${item.id}`} role="option" aria-selected={index === current} className={styles.choice} data-active={index === current} onClick={item.run}>
                  <span>{item.label}</span>
                  <span className={styles.path}>{item.detail}</span>
                </div>
              ))}
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function commands(mode: ViewMode, go: (to: string) => void, choose: (mode: ViewMode) => void): Command[] {
  const desks = visibleNav(mode).flatMap((group) => group.items)
    .map((item) => ({ id: `desk${item.to.replaceAll("/", "-")}`, label: item.label, detail: item.to, run: (): void => go(item.to) }));
  const views = VIEW_MODES.filter((item) => item.mode !== mode)
    .map((item) => ({ id: `mode-${item.mode}`, label: `${item.label} view`, detail: item.detail, run: (): void => choose(item.mode) }));
  return [...desks, ...views];
}
