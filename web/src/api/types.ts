import type { ViewMode } from "../lib/viewMode";

export type PrinterRef = { name: string; uri: string };
export type ScannerRef = { device: string; uri: string };
export type ProfileRef = { cell_size_px: number; num_symbols: number; print_dpi: number };
export type HealthBrief = { sha256: string; filename: string; health: number; status: string };

export type HomePayload = {
  printer: PrinterRef;
  scanner: ScannerRef;
  profile: ProfileRef | null;
  health: { tracked: number; flagged: number };
  newest_print: { job_id: string; source_file: string; pages: number } | null;
  newest_scan: { job_id: string; pages: number; created: string } | null;
  latest_check: (HealthBrief & { time: string }) | null;
  attention: HealthBrief[];
};

export type FileMeta = {
  name: string;
  size: number;
  sha256: string;
  type: string;
  hex: string;
  text: string | null;
};

export type InboxFile = { file_id: string; name: string; size: number; sha256: string };
export type TaskStart = { task_id: string };

export type PickValue = string | number | boolean;
export type Picks = Record<string, PickValue>;
export type EncodeOption = { label: string; value: PickValue };
export type EncodeField = {
  key: string;
  label: string;
  level: ViewMode;
  kind: "select" | "switch";
  hint: string;
  options: EncodeOption[];
};

export type EncodeOptions = {
  fields: EncodeField[];
  defaults: Picks;
  profile: "defaults" | "profile" | "edited";
};

export type EncodePlan = {
  filename: string;
  file_bytes: number;
  payload_bytes: number;
  sha256: string;
  data_pages: number;
  parity_pages: number;
  total_pages: number;
  capacity_bytes: number;
  ecc_sym: number;
  cell_size_px: number;
  grid: [number, number];
  sides: number;
  sheets: number;
  fill_sheets: boolean;
  fill_priority: string;
  passphrase_required?: boolean;
  requested?: { ecc_sym: number; cell_size_px: number; parity_pages: number };
  palette: number[][];
};

export type Box = { x: number; y: number; w: number; h: number };

export type EncodeGeometry = {
  page: { w: number; h: number };
  margins: Box;
  cell: number;
  grid: { cols: number; rows: number };
  slots: { block: Box; qr: Box; calibration: Box }[];
  tags: { id: number; x: number; y: number; size: number }[];
};

export type EncodePreview = {
  preview_id: string;
  plan: EncodePlan;
  geometry: EncodeGeometry;
  page: number;
  image: string;
};

export type PreviewRequest = {
  file_id: string | null;
  picks: Picks;
  page: number;
  passphrase?: string;
};

export type PrintJobSummary = {
  job_id: string;
  source_file: string;
  created: string;
  paper_size: string;
  pages: number;
  data_pages: number;
  total_pages: number;
  original_sha256: string;
  duplex: boolean;
  sides: number;
  printed: number;
};

export type PrintJobDetail = PrintJobSummary & { page_names: string[] };

export type PrinterChoice = { name: string; uri: string; state: string };
export type PrintersPayload = { printers: PrinterChoice[]; selected: string | null };

export type ScanSummary = { job_id: string; pages: number; created: string; sha256?: string };

export type DamagePage = {
  index: number;
  damaged: number;
  rebuilt: boolean;
  damage_map: number[][];
};
