import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { Link, useParams } from "react-router-dom";
import { queries } from "../../api/queries";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import { LibraryRecords } from "./LibraryRecords";
import { timelineLines } from "./timeline";

export function LibraryDetailPage(): ReactElement {
  const { sha = "" } = useParams();
  const query = useQuery(queries.libraryDoc(sha));
  return (
    <QueryGate query={query} loading="Opening the file" errorTitle="This file is not in the library">
      {(detail) => (
        <section className={view.stack}>
          <PageHeader kicker="Library" title={detail.filename}>
            <Link className={ui.quiet} to={`/health/${detail.sha256}`}>Health</Link>
          </PageHeader>
          <div className={view.split}>
            <LibraryRecords key={detail.sha256} detail={detail} />
            <section className={ui.card}>
              <p className={ui.kicker}>Timeline</p>
              {timelineLines(detail).map((line) => <p key={line}>{line}</p>)}
            </section>
          </div>
        </section>
      )}
    </QueryGate>
  );
}
