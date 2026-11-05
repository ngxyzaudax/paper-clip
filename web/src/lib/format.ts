export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 1024) return `${Math.max(0, Math.round(bytes))} B`;
  const units = ["KB", "MB", "GB", "TB"];
  const power = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length);
  const scaled = bytes / 1024 ** power;
  const digits = scaled >= 10 ? 0 : 1;
  return `${scaled.toFixed(digits)} ${units[power - 1] ?? "KB"}`;
}

export function formatHealth(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatDelta(value: number | null): string {
  if (value === null) return "First check";
  const rounded = value.toFixed(1);
  return value > 0 ? `+${rounded}` : rounded;
}

export function formatWhen(stamp: string): string {
  const date = new Date(stamp);
  if (Number.isNaN(date.getTime())) return stamp;
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export function shortSha(sha: string): string {
  if (sha.length <= 14) return sha;
  return `${sha.slice(0, 8)}…${sha.slice(-4)}`;
}

export function rgbCss(channels: number[]): string {
  const scale = channels.every((channel) => channel <= 1) ? 255 : 1;
  const red = Math.round((channels[0] ?? 0) * scale);
  const green = Math.round((channels[1] ?? 0) * scale);
  const blue = Math.round((channels[2] ?? 0) * scale);
  return `rgb(${red}, ${green}, ${blue})`;
}

export function asUrl(path: string): string {
  if (path.startsWith("http") || path.startsWith("/")) return path;
  return `/${path}`;
}

export function counted(amount: number, noun: string): string {
  return amount === 1 ? `${amount} ${noun}` : `${amount} ${noun}s`;
}

export function sheetCount(pages: number, duplex: boolean): number {
  return duplex ? Math.ceil(pages / 2) : pages;
}
