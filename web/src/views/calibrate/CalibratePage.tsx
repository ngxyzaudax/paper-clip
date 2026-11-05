import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { getJson } from "../../api/client";
import type { CalibrateState } from "../../api/careTypes";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import view from "../../styles/view.module.css";
import { CalibrateStudio } from "./CalibrateStudio";

export function CalibratePage(): ReactElement {
  const query = useQuery({ queryKey: ["calibrate"], queryFn: (): Promise<CalibrateState> => getJson<CalibrateState>("/api/calibrate") });
  return (
    <section className={view.stack}>
      <PageHeader kicker="Setup" title="Calibrate" lede="Print a test sheet, scan it, and save the density profile." />
      <QueryGate query={query} loading="Reading the session" errorTitle="Calibration status failed">
        {(state) => <CalibrateStudio state={state} onRefresh={(): void => void query.refetch()} />}
      </QueryGate>
    </section>
  );
}
