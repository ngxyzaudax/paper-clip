import { shows } from "../../lib/viewMode";
import type { ViewMode } from "../../lib/viewMode";

export type NavItem = { to: string; label: string; end?: boolean; level: ViewMode };
export type NavGroup = { label: string; items: NavItem[] };

export const NAV: NavGroup[] = [
  {
    label: "Start",
    items: [
      { to: "/", label: "Home", end: true, level: "simple" },
      { to: "/library", label: "Library", level: "simple" },
      { to: "/archive", label: "Archive", level: "simple" },
    ],
  },
  {
    label: "Workflow",
    items: [
      { to: "/encode", label: "Encode", level: "simple" },
      { to: "/print", label: "Print", level: "simple" },
      { to: "/decode", label: "Scan and decode", level: "simple" },
    ],
  },
  { label: "Care", items: [{ to: "/health", label: "Health", level: "simple" }] },
  {
    label: "Setup",
    items: [
      { to: "/devices", label: "Devices", level: "simple" },
      { to: "/calibrate", label: "Calibrate", level: "advanced" },
    ],
  },
];

export function flatNav(): NavItem[] {
  return NAV.flatMap((group) => group.items);
}

export function visibleNav(mode: ViewMode): NavGroup[] {
  return NAV.map((group) => ({ ...group, items: group.items.filter((item) => shows(mode, item.level)) }))
    .filter((group) => group.items.length > 0);
}
