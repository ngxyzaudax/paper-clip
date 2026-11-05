const THEME_KEY = "paper-clip-theme";

export type ThemeName = "light" | "dark";

export function storedTheme(): ThemeName {
  try {
    return localStorage.getItem(THEME_KEY) === "dark" ? "dark" : "light";
  } catch {
    return "light";
  }
}

export function applyStoredTheme(): ThemeName {
  const theme = storedTheme();
  document.documentElement.dataset.theme = theme;
  return theme;
}

export function storeTheme(theme: ThemeName): void {
  localStorage.setItem(THEME_KEY, theme);
  document.documentElement.dataset.theme = theme;
}
