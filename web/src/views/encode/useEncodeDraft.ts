import { useState } from "react";
import type { EncodeOptions, Picks } from "../../api/types";
import { allLayers } from "./layers";
import type { LayerFlags, LayerName } from "./layers";
import { marginOf, optionValue, picksFrom } from "./previewRequest";

export type EncodeDraft = {
  fileId: string | null;
  picks: Picks;
  margin: number;
  page: number;
  passphrase: string;
  layers: LayerFlags;
  setFile: (fileId: string) => void;
  setPick: (key: string, value: string | boolean) => void;
  setMargin: (margin: number) => void;
  setPage: (page: number) => void;
  setPassphrase: (value: string) => void;
  toggleLayer: (key: LayerName) => void;
  applyDefaults: (options: EncodeOptions) => void;
};

export function useEncodeDraft(options: EncodeOptions): EncodeDraft {
  const [fileId, setFileId] = useState<string | null>(null);
  const [picks, setPicks] = useState<Picks>(() => picksFrom(options.defaults));
  const [margin, setMargin] = useState<number>(() => marginOf(options.defaults));
  const [page, setPage] = useState(0);
  const [passphrase, setPassphrase] = useState("");
  const [layers, setLayers] = useState<LayerFlags>(allLayers);
  return {
    fileId, picks, margin, page, passphrase, layers,
    setFile: (next: string): void => {
      setFileId(next);
      setPage(0);
    },
    setPick: (key: string, value: string | boolean): void => {
      const field = options.fields.find((item) => item.key === key);
      setPicks((current) => ({ ...current, [key]: optionValue(field, value) }));
    },
    setMargin, setPage, setPassphrase,
    toggleLayer: (key: LayerName): void => setLayers((current) => ({ ...current, [key]: !current[key] })),
    applyDefaults: (fresh: EncodeOptions): void => {
      setPicks(picksFrom(fresh.defaults));
      setMargin(marginOf(fresh.defaults));
    },
  };
}
