import type { ReactElement } from "react";
import { Link } from "react-router-dom";
import type { HomePayload } from "../../api/types";
import { counted, formatWhen } from "../../lib/format";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";

export function HomeCards(props: { home: HomePayload }): ReactElement {
  return (
    <div className={view.cards}>
      {cards(props.home).map((card) => (
        <Link key={card.kicker} className={`${ui.card} ${view.cardLink}`} to={card.to}>
          <p className={ui.kicker}>{card.kicker}</p>
          <h2>{card.title}</h2>
          <p>{card.detail}</p>
        </Link>
      ))}
    </div>
  );
}

function cards(home: HomePayload): { kicker: string; title: string; detail: string; to: string }[] {
  return [
    { kicker: "Encode", title: "Colour the file", detail: "Turn a file into coloured dots on paper.", to: "/encode" },
    printCard(home),
    scanCard(home),
    decodeCard(home),
    healthCard(home),
    { kicker: "Archive", title: "Sheets and scans", detail: "See every printed sheet and every scan.", to: "/archive" },
  ];
}

function printCard(home: HomePayload): { kicker: string; title: string; detail: string; to: string } {
  const job = home.newest_print;
  return { kicker: "Print", title: job?.source_file || "No print yet", detail: job ? counted(job.pages, "page") : "Nothing has been printed yet.", to: job ? `/print?job=${encodeURIComponent(job.job_id)}` : "/print" };
}

function scanCard(home: HomePayload): { kicker: string; title: string; detail: string; to: string } {
  const job = home.newest_scan;
  return { kicker: "Scan", title: job ? `Scan · ${formatWhen(job.created)}` : "No scan yet", detail: job ? counted(job.pages, "page") : "Capture a printed sheet.", to: job ? `/decode/${encodeURIComponent(job.job_id)}` : "/decode" };
}

function decodeCard(home: HomePayload): { kicker: string; title: string; detail: string; to: string } {
  const check = home.latest_check;
  return { kicker: "Decode", title: check?.filename || "Nothing recovered", detail: check ? healthWords(check.status) : "Read a scan back into a file.", to: check ? `/health/${check.sha256}` : "/decode" };
}

function healthCard(home: HomePayload): { kicker: string; title: string; detail: string; to: string } {
  const tracked = home.health.tracked;
  const worn = home.health.flagged === 0 && home.latest_check?.status === "Worn";
  const title = home.health.flagged > 0 ? `${home.health.flagged} need a new copy` : worn ? "Worn, still readable" : tracked === 0 ? "No files yet" : `${tracked} readable`;
  return { kicker: "Health", title, detail: tracked === 0 ? "No files on paper yet" : `${tracked} ${tracked === 1 ? "file" : "files"} on paper`, to: "/health" };
}

function healthWords(status: string): string {
  if (status === "Worn") return "Worn, still readable";
  if (status === "Healthy") return "Readable";
  return status;
}
