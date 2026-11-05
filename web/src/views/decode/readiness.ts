import type { Readiness } from "../../api/careTypes";

export function readinessCopy(readiness: Readiness): { text: string; warn: string } {
  const pages = pageList(readiness.missing);
  if (readiness.state === "ready") return { text: "Every page is present.", warn: "" };
  if (readiness.state === "parity") return { text: `The missing ${pages} can be rebuilt, so you can decode now.`, warn: "A rebuilt page limits the health reading. Scan that side if you want the full reading." };
  return { text: `Still missing ${pages}.`, warn: "" };
}

function pageList(indexes: number[]): string {
  if (indexes.length === 0) return "the missing pages";
  const numbers = indexes.map((index) => String(index + 1));
  return `${numbers.length === 1 ? "page" : "pages"} ${numbers.join(", ")}`;
}
