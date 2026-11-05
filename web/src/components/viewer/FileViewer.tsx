import type { ReactElement } from "react";
import type { FileMeta } from "../../api/types";
import { FactList } from "../ui/FactList";
import { formatBytes } from "../../lib/format";
import { plainPage } from "./artifactPages";
import { PageViewer } from "./PageViewer";
import styles from "./viewer.module.css";

export function FileViewer(props: { meta: FileMeta; src: string }): ReactElement {
  return (
    <article className={styles.file}>
      <FactList rows={fileFacts(props.meta)} />
      <FileBody meta={props.meta} src={props.src} />
    </article>
  );
}

function fileFacts(meta: FileMeta): { label: string; value: string }[] {
  return [
    { label: "Name", value: meta.name },
    { label: "Size", value: formatBytes(meta.size) },
    { label: "Type", value: meta.type },
    { label: "SHA-256", value: meta.sha256 },
  ];
}

function FileBody(props: { meta: FileMeta; src: string }): ReactElement {
  if (props.meta.type.startsWith("image/")) return <PageViewer pages={[plainPage(props.src, props.meta.name)]} />;
  if (props.meta.type === "application/pdf") return <div className={styles.frameBox}><iframe sandbox="" src={props.src} title={props.meta.name} /></div>;
  if (props.meta.text !== null) return <div className={styles.frameBox}><pre>{props.meta.text}</pre></div>;
  return <div className={styles.frameBox}><pre>{props.meta.hex}</pre></div>;
}
