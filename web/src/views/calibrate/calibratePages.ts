import type { CalibrateState, CalPatch } from "../../api/careTypes";
import type { OverlayLayer, ViewerPage } from "../../components/viewer/types";

type SheetSide = { label: string; url: string | null; patches: CalPatch[] };

export function sheetSides(state: CalibrateState): SheetSide[] {
  return [
    { label: "Front sheet", url: state.front_url, patches: state.patches.front },
    { label: "Back sheet", url: state.back_url, patches: state.patches.back },
  ];
}

export function calibratePages(state: CalibrateState): ViewerPage[] {
  const sheets = sheetSides(state).filter((side) => side.url).map((side) => sheetPage(side));
  const scans = state.session_scans.map((scan): ViewerPage => ({
    ...artifactLike(scan.url),
    label: `Scan · ${scan.side}`,
    rotation: scan.rotation,
    note: `${scan.name} · ${scan.patches} patches read`,
  }));
  return [...sheets, ...scans];
}

export function patchOverlays(state: CalibrateState): (index: number) => OverlayLayer[] {
  const sides = sheetSides(state).filter((side) => side.url);
  return (index: number): OverlayLayer[] => {
    const side = sides[index];
    return side ? [{ name: "patches", rects: side.patches.map(patchRect) }] : [];
  };
}

export function patchSummary(patches: CalPatch[]): string {
  const read = patches.filter((patch) => patch.read);
  const passed = read.filter((patch) => patch.passed);
  return read.length === 0 ? `${patches.length} patches, not scanned yet` : `${passed.length} of ${read.length} read patches passed`;
}

function sheetPage(side: SheetSide): ViewerPage {
  return { ...artifactLike(side.url ?? ""), label: side.label, note: patchSummary(side.patches) };
}

function artifactLike(url: string): Omit<ViewerPage, "label"> {
  return { src: `${url}?size=1600`, thumb: `${url}?size=320`, hires: `${url}?size=3200`, original: url, crop: `${url}/crop` };
}

function patchRect(patch: CalPatch): OverlayLayer["rects"][number] {
  const tone = patch.read ? (patch.passed ? "pass" : "fail") : "unread";
  const verdict = patch.read ? (patch.passed ? "passed" : "failed") : "not read";
  return { x: patch.x, y: patch.y, w: patch.w, h: patch.h, tone, label: `${patch.name} · ${verdict}` };
}
