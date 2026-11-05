import { useEffect, useRef } from "react";
import type { TaskView } from "../lib/task";

export function useFinished(view: TaskView, onDone: () => void): void {
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;
  useEffect(() => {
    if (view.status === "done") onDoneRef.current();
  }, [view.status, view.data]);
}
