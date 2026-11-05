import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { Link } from "react-router-dom";
import { getJson } from "../../api/client";
import type { HomePayload } from "../../api/types";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import { AttentionList } from "./AttentionList";
import { HomeCards } from "./HomeCards";

export function HomePage(): ReactElement {
  const query = useQuery({ queryKey: ["home"], queryFn: (): Promise<HomePayload> => getJson<HomePayload>("/api/home") });
  return (
    <section className={view.stack}>
      <PageHeader kicker="Start" title="Paper-Clip" lede="Store a file on paper, and know when the paper starts to fail.">
        <Link className={ui.primary} to="/encode">Encode a file</Link>
        <Link className={ui.quiet} to="/decode">Scan and decode</Link>
      </PageHeader>
      <QueryGate query={query} loading="Opening home" errorTitle="Home could not load">
        {(home) => (
          <>
            <HomeCards home={home} />
            <section className={ui.card}>
              <p className={ui.kicker}>Attention</p>
              <AttentionList rows={home.attention} />
            </section>
          </>
        )}
      </QueryGate>
    </section>
  );
}
