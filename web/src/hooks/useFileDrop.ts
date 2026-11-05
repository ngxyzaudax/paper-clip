import { useState } from "react";
import type { ChangeEvent, DragEvent } from "react";

export type FileDrop = {
  hot: boolean;
  zone: {
    onDragOver: (event: DragEvent<HTMLElement>) => void;
    onDragLeave: () => void;
    onDrop: (event: DragEvent<HTMLElement>) => void;
  };
  onInput: (event: ChangeEvent<HTMLInputElement>) => void;
};

export function useFileDrop(onFiles: (files: File[]) => void): FileDrop {
  const [hot, setHot] = useState(false);
  return {
    hot,
    zone: {
      onDragOver: (event: DragEvent<HTMLElement>): void => {
        event.preventDefault();
        setHot(true);
      },
      onDragLeave: (): void => setHot(false),
      onDrop: (event: DragEvent<HTMLElement>): void => {
        event.preventDefault();
        setHot(false);
        deliver(event.dataTransfer.files, onFiles);
      },
    },
    onInput: (event: ChangeEvent<HTMLInputElement>): void => {
      deliver(event.target.files, onFiles);
      event.target.value = "";
    },
  };
}

function deliver(list: FileList | null, onFiles: (files: File[]) => void): void {
  const files = list ? [...list] : [];
  if (files.length > 0) onFiles(files);
}
