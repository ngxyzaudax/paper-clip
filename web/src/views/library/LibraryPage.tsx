import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { Link } from "react-router-dom";
import { getJson } from "../../api/client";
import { counted } from "../../lib/format";
import type { LibraryIndex, UnlinkedItem } from "../../api/careTypes";
import { Band } from "../../components/ui/Band";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import { StatusNote } from "../../components/ui/StatusNote";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";

export function LibraryPage(): ReactElement {
  const query = useQuery({ queryKey: ["library"], queryFn: (): Promise<LibraryIndex> => getJson<LibraryIndex>("/api/library") });
  return (
    <section className={view.stack}>
      <PageHeader kicker="Start" title="Library" lede="Every file that has been printed, scanned, or recovered." />
      <QueryGate query={query} loading="Opening the library" errorTitle="The library failed" isEmpty={(data) => data.documents.length === 0 && data.unlinked.length === 0} empty={<StatusNote tone="empty" title="The library is empty" />}>
        {(data) => (
          <>
            <div className={view.cards}>
              {data.documents.map((doc) => (
                <Link key={doc.sha256} className={`${ui.card} ${view.cardLink}`} to={`/library/${doc.sha256}`}>
                  <h2>{doc.filename}</h2>
                  <p>{counted(doc.pages, "page")}</p>
                  {doc.status ? <Band status={doc.status} /> : null}
                </Link>
              ))}
            </div>
            {data.unlinked.length > 0 ? <Unlinked rows={data.unlinked} /> : null}
          </>
        )}
      </QueryGate>
    </section>
  );
}

function Unlinked(props: { rows: UnlinkedItem[] }): ReactElement {
  return (
    <section className={ui.card}>
      <p className={ui.kicker}>Not matched to a file</p>
      <div className={view.list}>
        {props.rows.map((item) => <Link key={`${item.kind}-${item.id}`} to={unlinkedPath(item)}>{item.label}</Link>)}
      </div>
    </section>
  );
}

function unlinkedPath(item: UnlinkedItem): string {
  if (item.kind === "print") return `/print?job=${encodeURIComponent(item.id)}`;
  if (item.kind === "scan") return `/decode/${encodeURIComponent(item.id)}`;
  return "/library";
}
