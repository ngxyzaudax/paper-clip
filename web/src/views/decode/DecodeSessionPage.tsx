import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import type { ReactElement } from "react";
import { useParams } from "react-router-dom";
import { getJson } from "../../api/client";
import type { Wizard } from "../../api/careTypes";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import view from "../../styles/view.module.css";
import { DecodePanel } from "./DecodePanel";
import { PageBoard } from "./PageBoard";
import { ScanBar } from "./ScanBar";
import { ScanGuide } from "./ScanGuide";
import { ScanRows } from "./ScanRows";
import { ScanViewer } from "./ScanViewer";

export function DecodeSessionPage(): ReactElement {
  const { session = "" } = useParams();
  const [viewed, setViewed] = useState(0);
  const query = useQuery({
    queryKey: ["decode-session", session],
    queryFn: (): Promise<Wizard> => getJson<Wizard>(`/api/decode/sessions/${encodeURIComponent(session)}`),
    enabled: session.length > 0,
  });
  const refresh = (): void => void query.refetch();
  return (
    <section className={view.stack}>
      <PageHeader kicker="Workflow" title="Scan and decode" lede="Read the printed sheets back into the file." />
      <QueryGate query={query} loading="Opening the session" errorTitle="This scan session failed">
        {(wizard) => (
          <>
            <ScanGuide step={wizard.step} />
            <ScanBar jobId={wizard.job_id} onChanged={refresh} />
            <div className={view.split}>
              <PageBoard wizard={wizard} onView={setViewed} />
              <ScanRows wizard={wizard} viewed={wizard.scans[viewed]?.name ?? ""} onView={setViewed} onChanged={refresh} />
            </div>
            <ScanViewer wizard={wizard} index={viewed} onIndex={setViewed} />
            <DecodePanel wizard={wizard} />
          </>
        )}
      </QueryGate>
    </section>
  );
}
