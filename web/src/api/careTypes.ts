import type { CalibrationScan } from "./archiveTypes";
import type { ScanStep } from "./scanStep";
import type { DamagePage } from "./types";

export type { ScanStep };

export type { ArchiveGroup, ArchiveIndex, ArchiveKind, CalibrationScan } from "./archiveTypes";

export type ScanStatus = "pending" | "identified" | "unidentified" | "foreign" | "duplicate" | "two-pages";
export type ScanQuality = "pending" | "good" | "faint" | "reprint" | null;

export type ScanItem = {
  name: string;
  page_index: number | null;
  total_pages: number;
  sha256: string;
  rotation: number;
  status: ScanStatus;
  kept: boolean;
  quality: ScanQuality;
  erasures: number | null;
};

export type Readiness = {
  state: "missing" | "ready" | "parity";
  missing: number[];
  parity_pages: number;
};

export type Wizard = {
  job_id: string;
  duplex: boolean;
  print_job_id: string;
  sha256: string;
  total_pages: number;
  data_pages: number;
  passphrase_required: boolean;
  readiness: Readiness;
  next_prompt: string;
  step: ScanStep;
  scans: ScanItem[];
};

export type DecodeResult = {
  filename: string;
  saved_path: string;
  sha256: string;
  health: number;
  status: string;
  advice: string;
  lost: boolean;
  damage_pages: string[];
  pages: DamagePage[];
};

export type HealthRow = {
  sha256: string;
  filename: string;
  health: number;
  status: string;
  change: number | null;
  checks: number;
  time: string;
};

export type HealthReading = {
  time: string;
  health: number;
  status: string;
  advice: string;
  reader: string;
  damaged_bytes: number;
  payload_bytes: number;
  missing_pages: number[];
  pages: DamagePage[];
  damage_pages: string[];
  lost: boolean;
};

export type HealthDetail = {
  sha256: string;
  filename: string;
  size: number;
  trend: {
    since_previous: number | null;
    since_first: number | null;
    per_year: number | null;
    reaches_target: string | null;
  };
  readings: HealthReading[];
};

export type LibraryDocument = {
  sha256: string;
  filename: string;
  pages: number;
  health: number | null;
  status: string | null;
  job_id: string;
};

export type UnlinkedItem = { kind: string; id: string; label: string };

export type LibraryIndex = { documents: LibraryDocument[]; unlinked: UnlinkedItem[] };

export type LibraryPrint = { job_id: string; created: string; pages: number; data_pages: number; sides: number; paper_size: string; page_names: string[] };

export type LibraryScan = { job_id: string; pages: number; created: string; names: string[] };

export type LibraryDetail = {
  sha256: string;
  filename: string;
  prints: LibraryPrint[];
  scans: LibraryScan[];
  recovered: { job_id: string; name: string }[];
  readings: { time: string; health: number; status: string }[];
};

export type ScannerChoice = { device_id: string; vendor: string; model: string };

export type DevicesPayload = {
  printers: { name: string; uri: string; state: string }[];
  scanners: ScannerChoice[];
  printer_uri: string;
  scanner_id: string;
  printer_caps: Record<string, unknown>;
  scanner_caps: Record<string, unknown>;
};

export type CalPatch = { name: string; x: number; y: number; w: number; h: number; passed: boolean; read: boolean };

export type CalibrateState = {
  steps: { done: boolean; label: string }[];
  next_step: string;
  scans: string[];
  session_scans: CalibrationScan[];
  axes: { name: string; passed: string[]; failed: string[]; chosen: string }[];
  sheet_ready: boolean;
  profile_rows: { label: string; now: string; after: string }[] | null;
  front_url: string | null;
  back_url: string | null;
  sheet_px: { w: number; h: number };
  patches: { front: CalPatch[]; back: CalPatch[] };
};
