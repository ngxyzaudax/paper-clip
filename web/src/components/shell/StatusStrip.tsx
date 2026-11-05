import { useQuery } from "@tanstack/react-query";
import * as Tooltip from "@radix-ui/react-tooltip";
import type { ReactElement } from "react";
import { getJson } from "../../api/client";
import type { HomePayload } from "../../api/types";
import { classes } from "../../lib/classes";
import styles from "./shell.module.css";
import { ThemeToggle } from "./ThemeToggle";
import { ViewModeSwitch } from "./ViewModeSwitch";

export function StatusStrip(): ReactElement {
  const query = useQuery({ queryKey: ["home"], queryFn: (): Promise<HomePayload> => getJson<HomePayload>("/api/home") });
  return (
    <header className={styles.strip}>
      {query.data ? <StatusFacts home={query.data} /> : <p className={styles.muted}>{query.isError ? "Status unavailable" : "Reading status"}</p>}
      <span className={styles.spacer} />
      <ViewModeSwitch />
      <ThemeToggle />
    </header>
  );
}

function StatusFacts(props: { home: HomePayload }): ReactElement {
  const healthRisk = props.home.health.flagged > 0;
  return (
    <>
      <Fact label="Printer" value={props.home.printer.name || "No printer chosen"} tip={props.home.printer.name || "Choose one on the Devices desk"} />
      <Fact label="Scanner" value={scannerName(props.home)} tip={scannerName(props.home) === "No scanner chosen" ? "Choose one on the Devices desk" : scannerName(props.home)} />
      <Fact label="Profile" value={profileText(props.home)} tip={profileTip(props.home)} />
      <Fact label="Health" value={healthText(props.home)} tip={healthTip(props.home)} tone={healthRisk ? styles.risk : styles.ok} />
    </>
  );
}

function Fact(props: { label: string; value: string; tip: string; tone?: string }): ReactElement {
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <button type="button" className={styles.item}>
          <span className={styles.label}>{props.label}</span>
          <span className={classes(styles.value, props.tone)}>{props.value}</span>
        </button>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content className={styles.tip} sideOffset={8}>{props.tip}</Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

function profileText(home: HomePayload): string {
  if (!home.profile) return "Built-in setup";
  return `${home.profile.cell_size_px}-pixel dots · ${home.profile.num_symbols} colours`;
}

function profileTip(home: HomePayload): string {
  if (!home.profile) return "Built-in setup";
  return `Printer sharpness ${home.profile.print_dpi}`;
}

function scannerName(home: HomePayload): string {
  const value = home.scanner.device || home.scanner.uri;
  if (!value || value.startsWith("http")) return "No scanner chosen";
  return value;
}

function healthText(home: HomePayload): string {
  if (home.health.flagged > 0) return `${home.health.flagged} need a new copy`;
  if (home.latest_check?.status === "Worn") return "Worn, still readable";
  if (home.health.tracked === 0) return "No files yet";
  return `${home.health.tracked} readable`;
}

function healthTip(home: HomePayload): string {
  const files = `${home.health.tracked} ${home.health.tracked === 1 ? "file" : "files"} on paper`;
  return home.health.flagged > 0 ? `${home.health.flagged} need a new copy` : files;
}
