import type { ReactElement } from "react";
import { Link } from "react-router-dom";
import type { HealthBrief } from "../../api/types";
import { Band } from "../../components/ui/Band";
import { StatusNote } from "../../components/ui/StatusNote";
import view from "../../styles/view.module.css";

export function AttentionList(props: { rows: HealthBrief[] }): ReactElement {
  if (props.rows.length === 0) return <StatusNote tone="empty" title="No paper needs attention" detail="Nothing needs a new copy. Worn sheets can still be read." />;
  return (
    <div className={view.list}>
      {props.rows.map((row) => (
        <Link key={row.sha256} to={`/health/${row.sha256}`}>
          <Band status={row.status} /> {row.filename}
        </Link>
      ))}
    </div>
  );
}
