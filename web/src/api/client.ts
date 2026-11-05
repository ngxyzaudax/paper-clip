import { isRecord } from "../lib/record";
import { parseEvent } from "../lib/task";

const base = "";

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${base}${path}`);
  if (!response.ok) throw new Error(await errorDetail(response));
  return parseBody<T>(response);
}

export async function sendJson<T>(path: string, method: string, body?: unknown): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await errorDetail(response));
  return parseBody<T>(response);
}

export async function sendForm<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(`${base}${path}`, { method: "POST", body });
  if (!response.ok) throw new Error(await errorDetail(response));
  return parseBody<T>(response);
}

export function artifactUrl(kind: string, ident: string, name: string, size?: number): string {
  const path = `/api/artifacts/${kind}/${encodeURIComponent(ident)}/${encodeURIComponent(name)}`;
  return size === undefined ? path : `${path}?size=${size}`;
}

export function openEvents(taskId: string, onEvent: (event: string, data: Record<string, unknown>) => void): () => void {
  const source = new EventSource(`/api/tasks/${encodeURIComponent(taskId)}/events`);
  let closed = false;
  const finish = (): void => {
    closed = true;
    source.close();
  };
  const emit = (event: string, message: Event): void => {
    deliver(event, message, onEvent);
    if (event === "done" || event === "error") finish();
  };
  ["progress", "page", "done", "error"].forEach((event) => source.addEventListener(event, (message: Event) => emit(event, message)));
  source.onmessage = (message: MessageEvent<string>) => emit(eventName(message.data), message);
  source.onerror = () => {
    if (closed || source.readyState !== EventSource.CLOSED) return;
    onEvent("error", { message: "The task stream closed." });
  };
  return finish;
}

function deliver(event: string, message: Event, onEvent: (event: string, data: Record<string, unknown>) => void): void {
  const raw = (message as MessageEvent<string>).data;
  onEvent(event, parseEvent(typeof raw === "string" ? raw : ""));
}

function eventName(raw: string): string {
  const data = parseEvent(raw);
  return typeof data.event === "string" ? data.event : "progress";
}

async function parseBody<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) return undefined as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(text);
  }
}

async function errorDetail(response: Response): Promise<string> {
  const text = await response.text();
  const parsed = detailMessage(text);
  return parsed || text || response.statusText;
}

function detailMessage(text: string): string {
  try {
    const body: unknown = JSON.parse(text);
    if (!isRecord(body)) return "";
    return detailText(body.detail);
  } catch {
    return "";
  }
}

function detailText(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (!Array.isArray(detail)) return "";
  return detail.map(detailItem).filter(Boolean).join(", ");
}

function detailItem(item: unknown): string {
  if (typeof item === "string") return item;
  if (isRecord(item) && typeof item.msg === "string") return item.msg;
  return "";
}
