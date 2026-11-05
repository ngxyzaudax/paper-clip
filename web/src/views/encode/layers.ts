import type { EncodeGeometry } from "../../api/types";
import type { OverlayLayer } from "../../components/viewer/types";

export type LayerName = "margins" | "headers" | "qr" | "strips" | "tags";
export type LayerFlags = Record<LayerName, boolean>;

export const LAYER_NAMES: { key: LayerName; label: string }[] = [
  { key: "margins", label: "Blank edge" },
  { key: "headers", label: "Page label" },
  { key: "qr", label: "Page code" },
  { key: "strips", label: "Test strip" },
  { key: "tags", label: "Finder marks" },
];

export function allLayers(): LayerFlags {
  return { margins: true, headers: true, qr: true, strips: true, tags: true };
}

export function buildOverlays(geometry: EncodeGeometry, flags: LayerFlags): OverlayLayer[] {
  return [marginLayer(geometry, flags), headerLayer(geometry, flags), qrLayer(geometry, flags), stripLayer(geometry, flags), tagLayer(geometry, flags)].filter((layer): layer is OverlayLayer => layer !== null);
}

function marginLayer(geometry: EncodeGeometry, flags: LayerFlags): OverlayLayer | null {
  if (!flags.margins) return null;
  return { name: "margins", rects: [{ ...geometry.margins, label: "Margins" }] };
}

function headerLayer(geometry: EncodeGeometry, flags: LayerFlags): OverlayLayer | null {
  if (!flags.headers) return null;
  return { name: "headers", rects: geometry.slots.map((slot, index) => ({ ...slot.block, label: `Header ${index + 1}` })) };
}

function qrLayer(geometry: EncodeGeometry, flags: LayerFlags): OverlayLayer | null {
  if (!flags.qr) return null;
  return { name: "qr", rects: geometry.slots.map((slot, index) => ({ ...slot.qr, label: `QR ${index + 1}` })) };
}

function stripLayer(geometry: EncodeGeometry, flags: LayerFlags): OverlayLayer | null {
  if (!flags.strips) return null;
  return { name: "strips", rects: geometry.slots.map((slot, index) => ({ ...slot.calibration, label: `Strip ${index + 1}` })) };
}

function tagLayer(geometry: EncodeGeometry, flags: LayerFlags): OverlayLayer | null {
  if (!flags.tags) return null;
  return { name: "tags", rects: geometry.tags.map((tag) => ({ x: tag.x, y: tag.y, w: tag.size, h: tag.size, label: `Tag ${tag.id}` })) };
}
