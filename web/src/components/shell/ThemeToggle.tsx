import { Moon, Sun } from "lucide-react";
import { useState } from "react";
import type { ReactElement } from "react";
import { storeTheme, storedTheme } from "../../lib/theme";
import type { ThemeName } from "../../lib/theme";
import styles from "./shell.module.css";

export function ThemeToggle(): ReactElement {
  const [theme, setTheme] = useState<ThemeName>(storedTheme);
  function toggle(): void {
    const next: ThemeName = theme === "dark" ? "light" : "dark";
    storeTheme(next);
    setTheme(next);
  }
  const Icon = theme === "dark" ? Sun : Moon;
  return (
    <button type="button" className={styles.theme} onClick={toggle} aria-label={theme === "dark" ? "Use light paper" : "Use dark paper"}>
      <Icon size={14} strokeWidth={1.6} aria-hidden="true" />
      {theme === "dark" ? "Light" : "Dark"}
    </button>
  );
}
