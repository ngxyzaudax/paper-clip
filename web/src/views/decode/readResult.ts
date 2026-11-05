import type { DecodeResult } from "../../api/careTypes";
import type { DamagePage } from "../../api/types";
import { isRecord } from "../../lib/record";

export function readDecodeResult(data: Record<string, unknown> | null): DecodeResult | null {
  const source = unwrap(data);
  if (!source || typeof source.filename !== "string") return null;
  return {
    filename: source.filename,
    saved_path: text(source, "saved_path"),
    sha256: text(source, "sha256"),
    health: numberField(source, "health"),
    status: text(source, "status"),
    advice: text(source, "advice"),
    lost: source.lost === true,
    damage_pages: strings(source.damage_pages),
    pages: readPages(source.pages),
  };
}

function unwrap(data: Record<string, unknown> | null): Record<string, unknown> | null {
  if (!data) return null;
  if (typeof data.filename === "string") return data;
  return isRecord(data.result) ? data.result : null;
}

function text(data: Record<string, unknown>, key: string): string {
  return typeof data[key] === "string" ? data[key] : "";
}

function numberField(data: Record<string, unknown>, key: string): number {
  return typeof data[key] === "number" ? data[key] : 0;
}

function strings(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string");
}

function readPages(value: unknown): DamagePage[] {
  if (!Array.isArray(value)) return [];
  return value.filter(isRecord).map(readPage);
}

function readPage(value: Record<string, unknown>): DamagePage {
  return { index: numberField(value, "index"), damaged: numberField(value, "damaged"), rebuilt: value.rebuilt === true, damage_map: matrix(value.damage_map) };
}

function matrix(value: unknown): number[][] {
  if (!Array.isArray(value)) return [];
  return value.map(numberRow).filter((line) => line.length > 0);
}

function numberRow(value: unknown): number[] {
  if (!Array.isArray(value)) return [];
  return value.filter((cell): cell is number => typeof cell === "number");
}
