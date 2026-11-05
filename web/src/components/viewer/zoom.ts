const STEPS = [1, 1.25, 1.5, 2, 3];

export function nextZoom(current: number, direction: 1 | -1): number {
  const index = Math.max(0, STEPS.findIndex((step) => step >= current - 0.001));
  return STEPS[index + direction] ?? current;
}

export function zoomLabel(zoom: number): string {
  return zoom === 1 ? "Fit" : `${Math.round(zoom * 100)}%`;
}
