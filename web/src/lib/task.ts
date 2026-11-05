import { isRecord } from "./record";

export type TaskView = {
  status: "idle" | "running" | "done" | "error";
  progress: number | null;
  label: string;
  thumbs: string[];
  error: string;
  data: Record<string, unknown> | null;
};

export function idleTask(): TaskView {
  return { status: "idle", progress: null, label: "", thumbs: [], error: "", data: null };
}

export function runningTask(): TaskView {
  return { status: "running", progress: null, label: "", thumbs: [], error: "", data: null };
}

export function reduceTask(view: TaskView, event: string, data: Record<string, unknown>): TaskView {
  if (event === "progress") return progressView(view, data);
  if (event === "page") return pageView(view, data);
  if (event === "done") return { ...view, status: "done", progress: 1, data, label: textOf(data) || view.label };
  if (event === "error") return errorView(view, data);
  return view;
}

export function messageOf(data: Record<string, unknown> | null): string {
  if (!data || typeof data.message !== "string") return "";
  return data.message;
}

export function stringField(data: Record<string, unknown> | null, key: string): string {
  if (!data || typeof data[key] !== "string") return "";
  return data[key];
}

function errorView(view: TaskView, data: Record<string, unknown>): TaskView {
  if (view.status === "done") return view;
  return { ...view, status: "error", error: textOf(data) || "The task failed", data };
}

function progressView(view: TaskView, data: Record<string, unknown>): TaskView {
  return { ...view, status: "running", progress: fractionOf(data) ?? view.progress, label: textOf(data) || view.label };
}

function pageView(view: TaskView, data: Record<string, unknown>): TaskView {
  const url = typeof data.url === "string" ? data.url : "";
  const fresh = url !== "" && !view.thumbs.includes(url);
  return { ...view, label: textOf(data) || view.label, thumbs: fresh ? [...view.thumbs, url] : view.thumbs };
}

function textOf(data: Record<string, unknown>): string {
  const value = data.label ?? data.message ?? data.detail;
  return typeof value === "string" ? value : "";
}

function fractionOf(data: Record<string, unknown>): number | null {
  const raw = data.fraction ?? data.progress ?? data.percent;
  if (typeof raw !== "number" || Number.isNaN(raw)) return null;
  return raw > 1 ? raw / 100 : raw;
}

export function parseEvent(raw: string): Record<string, unknown> {
  try {
    const value: unknown = JSON.parse(raw);
    return isRecord(value) ? value : { value };
  } catch {
    return { message: raw };
  }
}
