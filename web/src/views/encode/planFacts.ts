import type { EncodePlan } from "../../api/types";
import { counted, formatBytes } from "../../lib/format";
import type { ViewMode } from "../../lib/viewMode";

type Fact = { label: string; value: string };
const GF_CODEWORD = 255;
const MAX_BLOCK = 200;
const SPARE_USE: Record<string, string> = {
  protection: "spent on surviving stains and tears",
  balanced: "split between strength and larger dots",
  dots: "spent on larger dots",
};

export function repairShare(ecc: number): number {
  const block = Math.min(MAX_BLOCK, GF_CODEWORD - ecc);
  return Math.floor(ecc / 2) / (block + ecc);
}

export function protectionText(plan: EncodePlan): string {
  if (!plan.filename) return "This is only the sheet layout. Add a file to see spare pages and how much damage the dots can take.";
  const share = Math.round(repairShare(plan.ecc_sym) * 100);
  const damage = `About ${share} in every 100 dots can be scratched and the page can still be read`;
  if (plan.parity_pages === 0) return `${damage}. There are no spare pages, so keep every page.`;
  const spare = plan.parity_pages === 1 ? "One lost or unreadable page" : `Up to ${plan.parity_pages} lost or unreadable pages`;
  return `${damage}. ${spare} can be rebuilt from a spare page.`;
}

export function sheetText(plan: EncodePlan): string {
  const sheets = `${plan.sheets} ${plan.sheets === 1 ? "sheet" : "sheets"}`;
  return `${sheets}, ${plan.sides === 2 ? "both sides" : "one side"}`;
}

export function planFacts(plan: EncodePlan, mode: ViewMode): Fact[] {
  const simple: Fact[] = [
    { label: "File", value: plan.filename ? `${plan.filename} · ${formatBytes(plan.file_bytes)}` : "No file yet" },
    { label: "Pages", value: `${counted(plan.data_pages, "page")} for the file, ${counted(plan.parity_pages, "spare page")}` },
  ];
  if (mode === "simple") return simple;
  const advanced: Fact[] = [
    ...simple,
    { label: "Packed file", value: plan.filename ? formatBytes(plan.payload_bytes) : "Nothing yet" },
    { label: "Room on each page", value: formatBytes(plan.capacity_bytes) },
    { label: "Repair in each patch", value: `${plan.ecc_sym} bytes` },
    { label: "Dot size", value: `${plan.cell_size_px} printer pixels` },
  ];
  if (mode === "advanced") return advanced;
  return [...advanced, ...expertFacts(plan)];
}

function askedText(requested: NonNullable<EncodePlan["requested"]>): string {
  return `${requested.ecc_sym} repair bytes, ${requested.cell_size_px}-pixel dots, ${counted(requested.parity_pages, "spare page")}`;
}

function expertFacts(plan: EncodePlan): Fact[] {
  const requested = plan.requested;
  return [
    { label: "Grid", value: `${plan.grid[0]} by ${plan.grid[1]} dots` },
    { label: "Spare room", value: plan.fill_sheets ? `On, ${SPARE_USE[plan.fill_priority] ?? plan.fill_priority}` : "Off" },
    ...(requested ? [{ label: "Before spare room", value: askedText(requested) }] : []),
    { label: "Passphrase", value: plan.passphrase_required ? "Required to read the pages" : "None. Anyone with this app can read the pages." },
    { label: "File check", value: plan.sha256 || "None yet" },
  ];
}
