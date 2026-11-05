import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { Link, useParams } from "react-router-dom";
import { queries } from "../../api/queries";
import type { HealthDetail } from "../../api/careTypes";
import { DamageGallery } from "../../components/damage/DamageGallery";
import { Band } from "../../components/ui/Band";
import { FactList } from "../../components/ui/FactList";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import { Reveal } from "../../components/ui/Reveal";
import { useShows } from "../../components/shell/ViewModeContext";
import { PageViewer } from "../../components/viewer/PageViewer";
import { formatBytes, formatDelta, formatHealth, formatWhen } from "../../lib/format";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import { comparePages } from "./comparePages";
import { HealthActions } from "./HealthActions";
import { HealthChart } from "./HealthChart";
import { HealthHistory } from "./HealthHistory";

export function HealthDetailPage(): ReactElement {
  const { sha = "" } = useParams();
  const query = useQuery(queries.healthDoc(sha));
  return (
    <QueryGate query={query} loading="Opening the record" errorTitle="This health record failed">
      {(detail) => <HealthRecord detail={detail} />}
    </QueryGate>
  );
}

function HealthRecord(props: { detail: HealthDetail }): ReactElement {
  const latest = props.detail.readings.at(-1);
  const compared = comparePages(props.detail.readings);
  const expert = useShows("expert");
  return (
    <section className={view.stack}>
      <PageHeader kicker="Care" title={props.detail.filename} lede={formatBytes(props.detail.size)}>
        {latest ? <Band status={latest.status} /> : null}
        <Link className={ui.quiet} to={`/library/${props.detail.sha256}`}>Library</Link>
      </PageHeader>
      {latest ? <p className={view.prompt}>{readingLine(latest.health, latest.advice, expert)}</p> : null}
      <Reveal at="advanced">
        <Trend detail={props.detail} />
      </Reveal>
      {latest ? <DamageGallery pages={latest.pages} images={latest.damage_pages} /> : null}
      <Reveal at="expert">
        {compared.length >= 2 ? <PageViewer pages={compared} /> : null}
      </Reveal>
      <Reveal at="advanced">
        <HealthHistory readings={props.detail.readings} />
      </Reveal>
      <HealthActions sha={props.detail.sha256} />
    </section>
  );
}

function readingLine(health: number, advice: string, expert: boolean): string {
  return expert ? `${formatHealth(health)} repair left. ${advice}` : advice;
}

function Trend(props: { detail: HealthDetail }): ReactElement {
  if (props.detail.readings.length < 2) return <p className={view.caption}>One check so far. Check again in a few months to see a trend and a reprint forecast.</p>;
  return (
    <>
      <FactList rows={trendFacts(props.detail)} />
      <HealthChart values={props.detail.readings.map((reading) => reading.health)} />
    </>
  );
}

function trendFacts(detail: HealthDetail): { label: string; value: string }[] {
  return [
    { label: "Since last", value: formatDelta(detail.trend.since_previous) },
    { label: "Since first", value: formatDelta(detail.trend.since_first) },
    { label: "Per year", value: formatDelta(detail.trend.per_year) },
    { label: "Forecast", value: detail.trend.reaches_target ? formatWhen(detail.trend.reaches_target) : "—" },
  ];
}
