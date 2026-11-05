import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { Link } from "react-router-dom";
import { getJson } from "../../api/client";
import type { HealthRow } from "../../api/careTypes";
import { Band } from "../../components/ui/Band";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import { StatusNote } from "../../components/ui/StatusNote";
import { useShows } from "../../components/shell/ViewModeContext";
import { formatDelta, formatHealth, formatWhen } from "../../lib/format";
import view from "../../styles/view.module.css";

export function HealthListPage(): ReactElement {
  const query = useQuery({ queryKey: ["health"], queryFn: (): Promise<HealthRow[]> => getJson<HealthRow[]>("/api/health") });
  const expert = useShows("expert");
  return (
    <section className={view.stack}>
      <PageHeader kicker="Care" title="Health" lede="Whether a paper copy is still readable. Print a fresh copy before this falls under 35%." />
      <QueryGate query={query} loading="Opening health" errorTitle="Health could not load" isEmpty={(rows) => rows.length === 0} empty={<StatusNote tone="empty" title="No paper copies yet" detail="Scan a printed sheet to start a record." />}>
        {(rows) => (
          <table className={view.table}>
            <thead>
              <tr><th>File</th><th>Status</th><th>When</th>{expert ? <><th>Repair left</th><th>Change</th><th>Checks</th></> : null}</tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.sha256}>
                  <td><Link to={`/health/${row.sha256}`}>{row.filename}</Link></td>
                  <td><Band status={row.status} /></td>
                  <td>{formatWhen(row.time)}</td>
                  {expert ? <><td>{formatHealth(row.health)}</td><td>{formatDelta(row.change)}</td><td>{row.checks}</td></> : null}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </QueryGate>
    </section>
  );
}
