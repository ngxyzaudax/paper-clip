import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { UseMutationResult } from "@tanstack/react-query";
import { useState } from "react";
import type { ReactElement } from "react";
import { getJson, sendJson } from "../../api/client";
import type { DevicesPayload } from "../../api/careTypes";
import { Reveal } from "../../components/ui/Reveal";
import { SelectField } from "../../components/ui/SelectField";
import { StatusNote } from "../../components/ui/StatusNote";
import ui from "../../styles/ui.module.css";
import view from "../../styles/view.module.css";
import styles from "../encode/encode.module.css";
import { DeviceCaps } from "./DeviceCaps";
import type { CapsQuery } from "./DeviceCaps";

type Option = { value: string; label: string };

export function DeviceForm(props: { devices: DevicesPayload; onSearch: () => void; searching: boolean }): ReactElement {
  const [printer, setPrinter] = useState(props.devices.printer_uri);
  const [scanner, setScanner] = useState(props.devices.scanner_id);
  const printerCaps = useCaps("printer", printer, props.devices.printer_uri === printer ? props.devices.printer_caps : undefined);
  const scannerCaps = useCaps("scanner", scanner, props.devices.scanner_id === scanner ? props.devices.scanner_caps : undefined);
  const save = useSave({ printer_uri: changedValue(printer, props.devices.printer_uri), scanner_id: changedValue(scanner, props.devices.scanner_id) });
  const changed = printer !== props.devices.printer_uri || scanner !== props.devices.scanner_id;
  return (
    <div className={view.split}>
      <div className={styles.column}>
        <DevicePick label="Printer" value={printer} onChange={setPrinter} options={printerOptions(props.devices)} empty="Turn it on and join this network, then search again." />
        <DevicePick label="Scanner" value={scanner} onChange={setScanner} options={scannerOptions(props.devices)} empty="Connect it by USB or network, then search again." />
        <div className={ui.actions}>
          <button type="button" className={ui.primary} disabled={!changed || save.isPending} onClick={(): void => save.mutate()}>Save</button>
          <button type="button" className={ui.quiet} disabled={props.searching} onClick={props.onSearch}>{props.searching ? "Searching" : "Search again"}</button>
        </div>
        {save.isError ? <StatusNote tone="error" title="Could not save devices" detail={save.error.message} /> : null}
        {save.isSuccess && !changed ? <StatusNote tone="empty" title="Saved" detail="This desk will use the chosen printer and scanner." /> : null}
      </div>
      <Reveal at="advanced">
        <div className={styles.column}>
          <DeviceCaps title="Printer" chosen={printer.length > 0} query={printerCaps} />
          <DeviceCaps title="Scanner" chosen={scanner.length > 0} query={scannerCaps} />
        </div>
      </Reveal>
    </div>
  );
}

function DevicePick(props: { label: string; value: string; onChange: (value: string) => void; options: Option[]; empty: string }): ReactElement {
  if (props.options.length === 0) return <StatusNote tone="empty" title={`${props.label} · none found`} detail={props.empty} />;
  return <SelectField label={props.label} value={props.value} onValueChange={props.onChange} options={props.options} />;
}

function useCaps(kind: "printer" | "scanner", ident: string, known: Record<string, unknown> | undefined): CapsQuery {
  const param = kind === "printer" ? "uri" : "device";
  return useQuery({
    queryKey: [`${kind}-caps`, ident],
    queryFn: (): Promise<Record<string, unknown>> => getJson(`/api/devices/${kind}?${param}=${encodeURIComponent(ident)}`),
    enabled: ident.length > 0,
    placeholderData: known,
  });
}

function changedValue(chosen: string, saved: string): string | null {
  return chosen && chosen !== saved ? chosen : null;
}

function useSave(selection: { printer_uri: string | null; scanner_id: string | null }): UseMutationResult<unknown, Error, void> {
  const client = useQueryClient();
  return useMutation<unknown, Error, void>({
    mutationFn: (): Promise<unknown> => sendJson("/api/devices", "POST", selection),
    onSuccess: async (): Promise<void> => {
      await client.invalidateQueries({ queryKey: ["devices"] });
      await client.invalidateQueries({ queryKey: ["home"] });
    },
  });
}

function printerOptions(devices: DevicesPayload): Option[] {
  return devices.printers.map((item) => ({ value: item.uri, label: printerLabel(item.name, item.state) }));
}

function printerLabel(name: string, state: string): string {
  const title = name.replaceAll("_", " ");
  const ready = state.toLowerCase();
  if (ready === "idle") return `${title} · Ready`;
  if (ready === "stopped") return `${title} · Stopped`;
  if (ready === "processing") return `${title} · Busy`;
  return title;
}

function scannerOptions(devices: DevicesPayload): Option[] {
  return devices.scanners.map((item) => ({ value: item.device_id, label: `${item.vendor} ${item.model}`.trim() || item.device_id }));
}
