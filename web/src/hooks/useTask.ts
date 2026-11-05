import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { openEvents } from "../api/client";
import { refreshAfterTask } from "../api/queries";
import { idleTask, reduceTask, runningTask } from "../lib/task";
import type { TaskView } from "../lib/task";

export type TaskRunner = {
  view: TaskView;
  start: (taskId: string) => void;
  reset: () => void;
};

export function useTask(): TaskRunner {
  const client = useQueryClient();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [view, setView] = useState<TaskView>(idleTask());
  useEffect(() => {
    if (!taskId) return;
    return openEvents(taskId, (event, data) => {
      setView((current) => reduceTask(current, event, data));
      if (event === "done" || event === "error") void refreshAfterTask(client);
    });
  }, [taskId, client]);
  return { view, start: begin(setTaskId, setView), reset: clear(setTaskId, setView) };
}

function begin(setTaskId: (id: string) => void, setView: (view: TaskView) => void): (taskId: string) => void {
  return (taskId: string): void => {
    setView(runningTask());
    setTaskId(taskId);
  };
}

function clear(setTaskId: (id: string | null) => void, setView: (view: TaskView) => void): () => void {
  return (): void => {
    setTaskId(null);
    setView(idleTask());
  };
}
