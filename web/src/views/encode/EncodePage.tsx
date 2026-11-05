import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { getJson } from "../../api/client";
import type { EncodeOptions } from "../../api/types";
import { PageHeader } from "../../components/ui/PageHeader";
import { QueryGate } from "../../components/ui/QueryGate";
import { EncodeStudio } from "./EncodeStudio";
import view from "../../styles/view.module.css";

export function EncodePage(): ReactElement {
  const options = useQuery({ queryKey: ["encode-options"], queryFn: (): Promise<EncodeOptions> => getJson<EncodeOptions>("/api/encode/options") });
  return (
    <section className={view.stack}>
      <PageHeader kicker="Workflow" title="Encode" lede="Turn a file into coloured dots on paper. Spare paper is used so a stained, torn, or missing sheet can still be read." />
      <QueryGate query={options} loading="Reading the saved setup" errorTitle="Encoding options failed">
        {(data) => <EncodeStudio options={data} />}
      </QueryGate>
    </section>
  );
}
