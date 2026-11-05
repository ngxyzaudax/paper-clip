import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { getJson } from "../../api/client";
import type { DevicesPayload } from "../../api/careTypes";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import view from "../../styles/view.module.css";
import { DeviceForm } from "./DeviceForm";

export function DevicesPage(): ReactElement {
  const query = useQuery({ queryKey: ["devices"], queryFn: (): Promise<DevicesPayload> => getJson<DevicesPayload>("/api/devices") });
  return (
    <section className={view.stack}>
      <PageHeader kicker="Setup" title="Devices" lede="Choose the printer and the scanner this desk will use." />
      <QueryGate query={query} loading="Looking for hardware" errorTitle="Device discovery failed">
        {(devices) => <DeviceForm devices={devices} searching={query.isFetching} onSearch={(): void => void query.refetch()} />}
      </QueryGate>
    </section>
  );
}
