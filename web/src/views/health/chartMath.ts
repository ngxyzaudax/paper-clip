const PAD = 10;

export function chartPoints(values: number[], width: number, height: number): string {
  return values.map((value, index) => `${xFor(index, values.length, width)},${yFor(value, height)}`).join(" ");
}

export function yFor(health: number, height: number): number {
  const clamped = Math.max(0, Math.min(100, health));
  return PAD + ((100 - clamped) / 100) * (height - PAD * 2);
}

function xFor(index: number, count: number, width: number): number {
  if (count <= 1) return width / 2;
  return PAD + (index / (count - 1)) * (width - PAD * 2);
}
