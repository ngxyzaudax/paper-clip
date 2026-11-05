import type { ScanItem, ScanStep } from "../../api/careTypes";

export type PageSlot = { sheet: number; side: "Front" | "Back" | "Sheet"; pageIndex: number };

export function pageSlots(total: number, duplex: boolean): PageSlot[] {
  return Array.from({ length: total }, (_, pageIndex): PageSlot => ({
    sheet: duplex ? Math.floor(pageIndex / 2) + 1 : pageIndex + 1,
    side: duplex ? (pageIndex % 2 === 0 ? "Front" : "Back") : "Sheet",
    pageIndex,
  }));
}

export function groupSheets(slots: PageSlot[]): { sheet: number; slots: PageSlot[] }[] {
  return slots.reduce<{ sheet: number; slots: PageSlot[] }[]>((groups, slot) => appendSlot(groups, slot), []);
}

export function slotCue(step: ScanStep, slot: { pageIndex: number; sheet: number }): boolean {
  if (step.action === "flip") return slot.pageIndex === step.page;
  if (step.action === "next" && step.side === "either") return slot.sheet === step.sheet;
  if (step.action === "next") return slot.pageIndex === step.page;
  return false;
}

export function keptFor(scans: ScanItem[], pageIndex: number): ScanItem | undefined {
  return scans.find((scan) => scan.kept && scan.page_index === pageIndex);
}

function appendSlot(groups: { sheet: number; slots: PageSlot[] }[], slot: PageSlot): { sheet: number; slots: PageSlot[] }[] {
  const last = groups.at(-1);
  if (!last || last.sheet !== slot.sheet) return [...groups, { sheet: slot.sheet, slots: [slot] }];
  return [...groups.slice(0, -1), { ...last, slots: [...last.slots, slot] }];
}
