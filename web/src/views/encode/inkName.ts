const NAMED: { name: string; red: number; green: number; blue: number }[] = [
  { name: "black", red: 0, green: 0, blue: 0 },
  { name: "cyan", red: 0, green: 255, blue: 255 },
  { name: "magenta", red: 255, green: 0, blue: 255 },
  { name: "yellow", red: 255, green: 255, blue: 0 },
  { name: "red", red: 255, green: 0, blue: 0 },
  { name: "green", red: 0, green: 255, blue: 0 },
  { name: "blue", red: 0, green: 0, blue: 255 },
  { name: "white", red: 255, green: 255, blue: 255 },
];

export function inkName(channels: number[]): string {
  const [red, green, blue] = scaled(channels);
  const exact = NAMED.find((ink) => ink.red === red && ink.green === green && ink.blue === blue);
  if (exact) return exact.name;
  if (red === green && green === blue) return grayName(red);
  return "mixed ink";
}

function scaled(channels: number[]): [number, number, number] {
  const scale = channels.every((channel) => channel <= 1) ? 255 : 1;
  return [Math.round((channels[0] ?? 0) * scale), Math.round((channels[1] ?? 0) * scale), Math.round((channels[2] ?? 0) * scale)];
}

function grayName(level: number): string {
  if (level < 80) return "near black";
  if (level > 200) return "near white";
  return "gray";
}
