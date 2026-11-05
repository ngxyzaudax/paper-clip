import { useCallback, useEffect, useState } from "react";
import type { ReactElement } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { flatNav } from "./nav";
import { Rail } from "./Rail";
import { StatusStrip } from "./StatusStrip";
import { useShellKeys } from "./useShellKeys";
import { useViewMode } from "./ViewModeContext";
import { CommandPalette } from "../ui/CommandPalette";
import { ShortcutDialog } from "../ui/ShortcutDialog";
import styles from "./shell.module.css";

export function AppShell(): ReactElement {
  const [palette, setPalette] = useState(false);
  const [help, setHelp] = useState(false);
  const location = useLocation();
  const { setMode } = useViewMode();
  const openPalette = useCallback((): void => setPalette(true), []);
  const openHelp = useCallback((): void => setHelp(true), []);
  useShellKeys(openPalette, openHelp, setMode);
  useEffect(() => {
    document.title = titleFor(location.pathname);
  }, [location.pathname]);
  return (
    <div className={styles.shell}>
      <Rail />
      <StatusStrip />
      <main className={styles.main}>
        <Outlet />
      </main>
      <CommandPalette open={palette} onOpenChange={setPalette} />
      <ShortcutDialog open={help} onOpenChange={setHelp} />
    </div>
  );
}

function titleFor(pathname: string): string {
  const item = flatNav().find((link) => pathname === link.to || (link.to !== "/" && pathname.startsWith(link.to)));
  return item ? `Paper-Clip · ${item.label}` : "Paper-Clip";
}
