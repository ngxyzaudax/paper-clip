export type ArchiveKind = "print" | "scan" | "calibration";

export type ArchiveGroup = {
  kind: ArchiveKind;
  ident: string;
  label: string;
  detail: string;
  created: string;
  names: string[];
};

export type ArchiveIndex = Record<ArchiveKind, ArchiveGroup[]>;

export type CalibrationScan = { name: string; side: string; rotation: number; patches: number; url: string };
