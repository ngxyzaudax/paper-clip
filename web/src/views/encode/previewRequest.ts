import type { EncodeField, EncodeOptions, PickValue, Picks, PreviewRequest } from "../../api/types";
import { shows } from "../../lib/viewMode";
import type { ViewMode } from "../../lib/viewMode";

export function previewRequest(input: { fileId: string | null; picks: Picks; margin: number; passphrase: string }): PreviewRequest {
  const picks = { ...input.picks, margin_mm: input.margin };
  const base = { file_id: input.fileId, picks, page: 0 };
  return input.passphrase ? { ...base, passphrase: input.passphrase } : base;
}

export function encodeBody(fileId: string, previewId: string, request: PreviewRequest): EncodeBody {
  return { file_id: fileId, preview_id: previewId, picks: request.picks, ...(request.passphrase ? { passphrase: request.passphrase } : {}) };
}

type EncodeBody = { file_id: string; preview_id: string; picks: Picks; passphrase?: string };

export function picksFrom(defaults: Picks): Picks {
  return Object.fromEntries(Object.entries(defaults).filter(([key]) => key !== "margin_mm"));
}

export function marginOf(defaults: Picks): number {
  const number = Number(defaults.margin_mm);
  return Number.isFinite(number) ? number : 0;
}

export function setupTitle(options: EncodeOptions, picks: Picks, margin: number): string {
  const current: Picks = { ...picks, margin_mm: margin };
  const same = Object.entries(options.defaults).every(([key, value]) => current[key] === value);
  if (!same) return "Edited";
  return options.profile === "profile" ? "Saved printer setup" : "Built-in setup";
}

export function visibleFields(options: EncodeOptions, mode: ViewMode): EncodeField[] {
  return options.fields.filter((field) => shows(mode, field.level));
}

export function hiddenEdits(options: EncodeOptions, picks: Picks, margin: number, mode: ViewMode): string[] {
  const fields = options.fields.filter((field) => !shows(mode, field.level) && picks[field.key] !== options.defaults[field.key]);
  const marginHidden = !shows(mode, "advanced") && margin !== marginOf(options.defaults);
  return [...fields.map((field) => field.label), ...(marginHidden ? ["Blank edge"] : [])];
}

export function optionValue(field: EncodeField | undefined, raw: string | boolean): PickValue {
  if (typeof raw === "boolean") return raw;
  const match = field?.options.find((option) => String(option.value) === raw);
  return match ? match.value : raw;
}
