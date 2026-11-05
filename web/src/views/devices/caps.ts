export function capError(caps: Record<string, unknown> | undefined): string {
  if (!caps || typeof caps.error !== "string") return "";
  return caps.error;
}

export function capSummary(caps: Record<string, unknown> | undefined): string {
  if (!caps || capError(caps)) return "";
  const paper = paperName(String(caps.media ?? ""));
  const colour = caps.color === "color" ? "colour" : caps.color === "monochrome" ? "black and white" : "";
  const parts = [paper, colour].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : "Ready";
}

function paperName(media: string): string {
  const name = media.toLowerCase();
  if (name.includes("a4")) return "A4";
  if (name.includes("letter")) return "Letter";
  return "";
}
