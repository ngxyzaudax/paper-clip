import * as Dialog from "@radix-ui/react-dialog";
import { useRef } from "react";
import type { ReactElement } from "react";
import ui from "../../styles/ui.module.css";
import styles from "./dialog.module.css";

export type ConfirmDialogProps = {
  open: boolean;
  title: string;
  body: string;
  confirmLabel: string;
  onConfirm: () => void;
  onOpenChange: (open: boolean) => void;
};

export function ConfirmDialog(props: ConfirmDialogProps): ReactElement {
  const cancelRef = useRef<HTMLButtonElement>(null);
  return (
    <Dialog.Root open={props.open} onOpenChange={props.onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className={styles.overlay} />
        <Dialog.Content className={styles.content} onOpenAutoFocus={focusCancel(cancelRef)}>
          <Dialog.Title className={styles.title}>{props.title}</Dialog.Title>
          <Dialog.Description className={styles.body}>{props.body}</Dialog.Description>
          <div className={styles.actions}>
            <button ref={cancelRef} type="button" className={ui.quiet} onClick={(): void => props.onOpenChange(false)}>Cancel</button>
            <button type="button" className={ui.primary} onClick={props.onConfirm}>{props.confirmLabel}</button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function focusCancel(cancelRef: { current: HTMLButtonElement | null }): (event: Event) => void {
  return (event: Event): void => {
    event.preventDefault();
    cancelRef.current?.focus();
  };
}
