export type ViewerPage = {
  src: string;
  label: string;
  thumb?: string;
  hires?: string;
  original?: string;
  crop?: string;
  rotation?: number;
  note?: string;
};

export type OverlayRect = { x: number; y: number; w: number; h: number; label?: string; tone?: string };
export type OverlayLayer = { name: string; rects: OverlayRect[] };

export type PageViewerProps = {
  pages: ViewerPage[];
  overlays?: OverlayLayer[] | ((index: number) => OverlayLayer[]);
  pageWidth?: number;
  pageHeight?: number;
  index?: number;
  onIndex?: (index: number) => void;
  empty?: string;
};
