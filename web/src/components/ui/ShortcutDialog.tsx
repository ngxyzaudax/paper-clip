import * as Dialog from "@radix-ui/react-dialog";
import type { ReactElement } from "react";
import ui from "../../styles/ui.module.css";
import styles from "./dialog.module.css";

const SHORTCUTS: { keys: string; action: string }[] = [
  { keys: "⌘K / Ctrl K", action: "Open the command palette" },
  { keys: "?", action: "Open this card" },
  { keys: "Alt 1 / 2 / 3", action: "Simple, Advanced, or Expert view" },
  { keys: "Space", action: "Scan the next sheet, on the scan wizard" },
];

export function ShortcutDialog(props: { open: boolean; onOpenChange: (open: boolean) => void }): ReactElement {
  return (
    <Dialog.Root open={props.open} onOpenChange={props.onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className={styles.overlay} />
        <Dialog.Content className={styles.content}>
          <Dialog.Title className={styles.title}>Keys</Dialog.Title>
          <Dialog.Description className={styles.body}>The press floor, from the keyboard.</Dialog.Description>
          <div className={styles.keys}>
            {SHORTCUTS.map((item) => (
              <div key={item.keys}>
                <kbd>{item.keys}</kbd>
                <span>{item.action}</span>
              </div>
            ))}
          </div>
          <div className={styles.actions}>
            <Dialog.Close className={ui.primary}>Close</Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
