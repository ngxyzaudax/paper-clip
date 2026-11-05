import type { ReactElement } from "react";
import { Link } from "react-router-dom";
import type { DecodeResult } from "../../api/careTypes";
import { DamageGallery } from "../../components/damage/DamageGallery";
import { Band } from "../../components/ui/Band";
import { StatusNote } from "../../components/ui/StatusNote";
import { DecodedFile } from "../../components/viewer/DecodedFile";
import { formatHealth } from "../../lib/format";
import ui from "../../styles/ui.module.css";
import { savedName } from "./scanPages";

export function DecodeOutcome(props: { jobId: string; result: DecodeResult }): ReactElement {
  if (props.result.lost) return <StatusNote tone="error" title="The file is lost" detail={props.result.advice} />;
  return (
    <section className={ui.card}>
      <Band status={props.result.status} />
      <p>{formatHealth(props.result.health)}</p>
      <p>{props.result.advice}</p>
      {props.result.saved_path ? <DecodedFile jobId={props.jobId} name={savedName(props.result.saved_path, props.result.filename)} /> : null}
      <DamageGallery pages={props.result.pages} images={props.result.damage_pages} />
      <div className={ui.row}>
        <Link className={ui.quiet} to={`/health/${props.result.sha256}`}>Health</Link>
        <Link className={ui.quiet} to={`/library/${props.result.sha256}`}>Library</Link>
      </div>
    </section>
  );
}
