import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { Link, NavLink, useParams } from "react-router-dom";
import { queries } from "../../api/queries";
import type { ArchiveGroup, ArchiveIndex, ArchiveKind } from "../../api/archiveTypes";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import { StatusNote } from "../../components/ui/StatusNote";
import { artifactPage } from "../../components/viewer/artifactPages";
import { PageViewer } from "../../components/viewer/PageViewer";
import { classes } from "../../lib/classes";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import { ARCHIVE_TABS, archiveKind, archivePath, chosenGroup, pageLabel } from "./archiveTabs";
import styles from "./archive.module.css";

export function ArchivePage(): ReactElement {
  const params = useParams();
  const kind = archiveKind(params.kind);
  const index = useQuery(queries.archive());
  return (
    <section className={view.stack}>
      <PageHeader kicker="Records" title="Archive" lede="Every data sheet, raw scan, and calibration sheet kept on this machine." />
      <nav className={styles.tabs} aria-label="Archive kind">
        {ARCHIVE_TABS.map((tab) => (
          <NavLink key={tab.kind} to={archivePath(tab.kind)} className={classes(ui.quiet, tab.kind === kind && styles.current)} aria-current={tab.kind === kind ? "page" : undefined}>
            {tab.label} {index.data ? <span className={styles.count}>{index.data[tab.kind].length}</span> : null}
          </NavLink>
        ))}
      </nav>
      <QueryGate query={index} loading="Reading the archive" errorTitle="The archive failed">
        {(data) => <ArchiveBody index={data} kind={kind} ident={params.ident} />}
      </QueryGate>
    </section>
  );
}

function ArchiveBody(props: { index: ArchiveIndex; kind: ArchiveKind; ident: string | undefined }): ReactElement {
  const group = chosenGroup(props.index, props.kind, props.ident);
  const empty = ARCHIVE_TABS.find((tab) => tab.kind === props.kind)?.empty ?? "";
  if (!group) return <StatusNote tone="empty" title="Nothing here yet" detail={empty} />;
  return (
    <div className={styles.layout}>
      <GroupList groups={props.index[props.kind]} chosen={group.ident} />
      <div className={view.stack}>
        <div className={styles.title}>
          <h2>{group.label}</h2>
          <p>{group.detail}</p>
        </div>
        {group.names.length > 0 ? <PageViewer pages={group.names.map((name, index) => artifactPage(group.kind, group.ident, name, pageLabel(group, name, index)))} /> : <StatusNote tone="empty" title="This record holds no images" />}
      </div>
    </div>
  );
}

function GroupList(props: { groups: ArchiveGroup[]; chosen: string }): ReactElement {
  return (
    <ul className={styles.groups} aria-label="Records">
      {props.groups.map((group) => (
        <li key={group.ident}>
          <Link to={archivePath(group.kind, group.ident)} className={classes(styles.group, group.ident === props.chosen && styles.current)} aria-current={group.ident === props.chosen ? "true" : undefined}>
            <strong>{group.label}</strong>
            <span>{group.detail}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
