import { Archive, Cable, Crosshair, Files, HeartPulse, Home, Library, Printer, ScanLine } from "lucide-react";
import type { ReactElement } from "react";
import { NavLink } from "react-router-dom";
import { classes } from "../../lib/classes";
import { visibleNav } from "./nav";
import { useViewMode } from "./ViewModeContext";
import styles from "./shell.module.css";

const ICONS: Record<string, typeof Home> = {
  "/": Home,
  "/library": Library,
  "/archive": Archive,
  "/encode": Files,
  "/print": Printer,
  "/decode": ScanLine,
  "/health": HeartPulse,
  "/devices": Cable,
  "/calibrate": Crosshair,
};

export function Rail(): ReactElement {
  const { mode } = useViewMode();
  return (
    <aside className={styles.rail}>
      <div className={styles.brand}>
        <div className={styles.brandRow}>
          <span className={styles.mark} aria-hidden="true" />
          <span className={styles.word}>Paper-Clip</span>
        </div>
        <div className={styles.rule} />
      </div>
      <nav className={styles.nav} aria-label="Desks">
        {visibleNav(mode).map((group) => (
          <div key={group.label}>
            <p className={styles.group}>{group.label}</p>
            {group.items.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => classes(styles.link, isActive && styles.active)}>
                <NavIcon path={item.to} />
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <p className={styles.hint}><kbd>?</kbd> keys · <kbd>⌘/Ctrl K</kbd> go</p>
    </aside>
  );
}

function NavIcon(props: { path: string }): ReactElement {
  const Icon = ICONS[props.path] ?? Home;
  return <Icon size={16} strokeWidth={1.6} aria-hidden="true" />;
}
