import { useEffect, useState } from "react";
import type { ViewerPage } from "./types";

export type ViewerState = {
  index: number;
  zoom: number;
  split: number;
  upright: boolean;
  loupe: boolean;
  select: (index: number) => void;
  setZoom: (zoom: number) => void;
  setSplit: (split: number) => void;
  toggleUpright: () => void;
  toggleLoupe: () => void;
};

export function useViewerState(pages: ViewerPage[], controlled?: number, onIndex?: (index: number) => void): ViewerState {
  const [own, setOwn] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [split, setSplit] = useState(0);
  const [upright, setUpright] = useState(true);
  const [loupe, setLoupe] = useState(false);
  const identity = pages.map((page) => page.src).join("|");
  useEffect(() => {
    setOwn(0);
    setZoom(1);
    setSplit(0);
  }, [identity]);
  const index = Math.min(Math.max(controlled ?? own, 0), Math.max(pages.length - 1, 0));
  return {
    index, zoom, split, upright, loupe,
    select: (next: number): void => {
      setSplit(0);
      setOwn(next);
      onIndex?.(next);
    },
    setZoom, setSplit,
    toggleUpright: (): void => setUpright((current) => !current),
    toggleLoupe: (): void => setLoupe((current) => !current),
  };
}
