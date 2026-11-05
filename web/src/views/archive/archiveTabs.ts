import type { ArchiveGroup, ArchiveIndex, ArchiveKind } from "../../api/archiveTypes";

export const ARCHIVE_TABS: { kind: ArchiveKind; label: string; empty: string }[] = [
  { kind: "print", label: "Data sheets", empty: "No sheets have been encoded yet." },
  { kind: "scan", label: "Raw scans", empty: "No scans have been captured yet." },
  { kind: "calibration", label: "Calibration", empty: "No calibration sheets or scans yet." },
];

export function archiveKind(raw: string | undefined): ArchiveKind {
  return ARCHIVE_TABS.find((tab) => tab.kind === raw)?.kind ?? "print";
}

export function archivePath(kind: ArchiveKind, ident?: string): string {
  return ident ? `/archive/${kind}/${encodeURIComponent(ident)}` : `/archive/${kind}`;
}

export function chosenGroup(index: ArchiveIndex, kind: ArchiveKind, ident: string | undefined): ArchiveGroup | undefined {
  const groups = index[kind];
  return groups.find((group) => group.ident === ident) ?? groups[0];
}

function calibrationLabel(name: string): string {
  const stem = name.replace(/\.[a-z]+$/i, "");
  if (stem.toLowerCase() === "front") return "Front";
  if (stem.toLowerCase() === "back") return "Back";
  return stem;
}

export function pageLabel(group: ArchiveGroup, name: string, index: number): string {
  if (group.kind === "calibration") return calibrationLabel(name);
  return `${group.kind === "scan" ? "Scan" : "Page"} ${index + 1}`;
}
