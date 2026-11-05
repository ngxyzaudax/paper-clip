import type { ReactElement } from "react";
import type { HealthReading } from "../../api/careTypes";
import { Band } from "../../components/ui/Band";
import { useShows } from "../../components/shell/ViewModeContext";
import { formatHealth, formatWhen } from "../../lib/format";
import view from "../../styles/view.module.css";

function misread(reading: HealthReading, expert: boolean): string {
  if (reading.payload_bytes <= 0 || reading.damaged_bytes <= 0) return "None";
  const share = reading.damaged_bytes / reading.payload_bytes;
  if (share < 0.01) return "Under 1% misread";
  if (!expert) return `About ${Math.max(1, Math.round(share * 100))}% misread`;
  return `${reading.damaged_bytes.toLocaleString()} of ${reading.payload_bytes.toLocaleString()} misread`;
}

export function HealthHistory(props: { readings: HealthReading[] }): ReactElement {
  const expert = useShows("expert");
  return (
    <table className={view.table}>
      <caption className={view.caption}>Every health check of this file, oldest first</caption>
      <thead>
        <tr>
          <th scope="col">When</th><th scope="col">Status</th>
          {expert ? <th scope="col">Repair left</th> : null}
          {expert ? <th scope="col">Reader</th> : null}
          <th scope="col">Misread</th><th scope="col">Missing pages</th>
        </tr>
      </thead>
      <tbody>
        {props.readings.map((reading) => (
          <tr key={reading.time}>
            <th scope="row">{formatWhen(reading.time)}</th>
            <td><Band status={reading.status} /></td>
            {expert ? <td>{formatHealth(reading.health)}</td> : null}
            {expert ? <td>{reading.reader === "cell model" ? "Automatic reader" : reading.reader}</td> : null}
            <td>{misread(reading, expert)}</td>
            <td>{reading.missing_pages.map((index) => index + 1).join(", ") || "None"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
