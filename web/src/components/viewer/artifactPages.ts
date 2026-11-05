import { artifactUrl } from "../../api/client";
import type { ViewerPage } from "./types";

export function artifactPage(kind: string, ident: string, name: string, label: string, rotation = 0): ViewerPage {
  const original = artifactUrl(kind, ident, name);
  return {
    src: artifactUrl(kind, ident, name, 1600),
    thumb: artifactUrl(kind, ident, name, 320),
    hires: artifactUrl(kind, ident, name, 3200),
    original,
    crop: `${original}/crop`,
    label,
    rotation,
  };
}

export function printPageLabel(index: number, dataPages: number): string {
  if (dataPages > 0 && index >= dataPages) return `Spare ${index - dataPages + 1}`;
  return `Page ${index + 1}`;
}

export function printPages(jobId: string, names: string[], dataPages: number): ViewerPage[] {
  return names.map((name, index) => artifactPage("print", jobId, name, printPageLabel(index, dataPages)));
}

export function plainPage(src: string, label: string): ViewerPage {
  return { src, label, thumb: src, original: src };
}
