import type { HealthReading } from "../../api/careTypes";
import type { ViewerPage } from "../../components/viewer/types";
import { formatWhen } from "../../lib/format";

export function comparePages(readings: HealthReading[]): ViewerPage[] {
  return readings.slice(-2).flatMap((reading) => {
    const src = reading.damage_pages[0];
    return src ? [{ src, label: formatWhen(reading.time) }] : [];
  });
}
