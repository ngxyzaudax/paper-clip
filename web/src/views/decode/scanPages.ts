import type { ScanItem, Wizard } from "../../api/careTypes";
import { artifactPage, printPageLabel } from "../../components/viewer/artifactPages";
import type { ViewerPage } from "../../components/viewer/types";

export function scanPages(wizard: Wizard): ViewerPage[] {
  return wizard.scans.map((scan) => ({
    ...artifactPage("scan", wizard.job_id, scan.name, scanLabel(scan, wizard.data_pages), scan.rotation),
    note: scanNote(scan),
  }));
}

const STATUS_TEXT: Record<string, string> = {
  pending: "Not read yet",
  unidentified: "Not matched to a page",
  "two-pages": "This photo shows two pages. Scan one side at a time.",
  foreign: "This sheet is from a different file. Set it aside.",
  unread: "Could not judge this scan. Close the lid and scan it again.",
  duplicate: "This page is already kept",
  identified: "Matched to a page",
};

export function scanLabel(scan: ScanItem, dataPages: number): string {
  return scan.page_index === null ? scanTitle(scan.name) : printPageLabel(scan.page_index, dataPages);
}

export function scanNote(scan: ScanItem): string {
  const status = STATUS_TEXT[scan.status] ?? scan.status;
  return scan.status === "duplicate" ? `${status} · not used` : status;
}

function scanTitle(name: string): string {
  const match = /^scan_(\d+)\.[a-z0-9]+$/i.exec(name);
  return match ? `Scan ${Number(match[1])}` : name;
}

export function scanIndexOf(wizard: Wizard, name: string): number {
  return wizard.scans.findIndex((scan) => scan.name === name);
}

export function savedName(savedPath: string, fallback: string): string {
  return savedPath.split(/[\\/]/).filter(Boolean).at(-1) ?? fallback;
}
