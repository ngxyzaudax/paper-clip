import type { UseQueryResult } from "@tanstack/react-query";
import type { ReactElement } from "react";
import type { EncodePreview } from "../../api/types";
import { printPageLabel } from "../../components/viewer/artifactPages";
import { PageViewer } from "../../components/viewer/PageViewer";
import type { ViewerPage } from "../../components/viewer/types";
import { QueryGate } from "../../components/ui/QueryGate";
import { Reveal } from "../../components/ui/Reveal";
import { useShows } from "../../components/shell/ViewModeContext";
import { classes } from "../../lib/classes";
import ui from "../../styles/ui.module.css";
import { buildOverlays, LAYER_NAMES } from "./layers";
import type { LayerFlags, LayerName } from "./layers";
import styles from "./encode.module.css";

const MAX_FILMSTRIP = 60;

export function EncodePreviewPane(props: {
  preview: UseQueryResult<EncodePreview, Error>;
  fileLoaded: boolean;
  page: number;
  layers: LayerFlags;
  onPage: (page: number) => void;
  onToggle: (key: LayerName) => void;
}): ReactElement {
  const layered = useShows("advanced");
  return (
    <div className={styles.column}>
      <Reveal at="advanced">
        <div className={ui.row} role="group" aria-label="Overlay layers">
          {LAYER_NAMES.map((layer) => (
            <button key={layer.key} type="button" className={classes(ui.quiet, props.layers[layer.key] && styles.pressed)} aria-pressed={props.layers[layer.key]} onClick={(): void => props.onToggle(layer.key)}>
              {layer.label}
            </button>
          ))}
        </div>
      </Reveal>
      <QueryGate query={props.preview} loading="Drawing the sheet" errorTitle="Preview failed">
        {(preview) => (
          <PageViewer
            pages={previewPages(preview, props.fileLoaded)}
            index={props.page}
            onIndex={props.onPage}
            overlays={layered ? buildOverlays(preview.geometry, props.layers) : []}
            pageWidth={preview.geometry.page.w}
            pageHeight={preview.geometry.page.h}
          />
        )}
      </QueryGate>
    </div>
  );
}

function previewPages(preview: EncodePreview, fileLoaded: boolean): ViewerPage[] {
  if (!fileLoaded) return [{ src: preview.image, label: "Layout preview", note: "drop a file to see its dots" }];
  const total = Math.min(preview.plan.total_pages, MAX_FILMSTRIP);
  return Array.from({ length: total }, (_, index) => {
    const src = `/api/media/preview/${preview.preview_id}/${index}.jpg`;
    const parity = index >= preview.plan.data_pages;
    return { src, thumb: src, label: printPageLabel(index, preview.plan.data_pages), note: parity ? "spare page" : undefined };
  });
}
