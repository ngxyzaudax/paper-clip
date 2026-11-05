import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as Tooltip from "@radix-ui/react-tooltip";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import type { ReactElement } from "react";
import { AppShell } from "./components/shell/AppShell";
import { ViewModeProvider } from "./components/shell/ViewModeContext";
import { StatusNote } from "./components/ui/StatusNote";
import { ArchivePage } from "./views/archive/ArchivePage";
import { CalibratePage } from "./views/calibrate/CalibratePage";
import { DecodeSessionPage } from "./views/decode/DecodeSessionPage";
import { DecodeSourcePage } from "./views/decode/DecodeSourcePage";
import { DevicesPage } from "./views/devices/DevicesPage";
import { EncodePage } from "./views/encode/EncodePage";
import { HealthDetailPage } from "./views/health/HealthDetailPage";
import { HealthListPage } from "./views/health/HealthListPage";
import { HomePage } from "./views/home/HomePage";
import { LibraryDetailPage } from "./views/library/LibraryDetailPage";
import { LibraryPage } from "./views/library/LibraryPage";
import { PrintPage } from "./views/print/PrintPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export function App(): ReactElement {
  return (
    <QueryClientProvider client={queryClient}>
      <ViewModeProvider>
        <Tooltip.Provider delayDuration={280}>
          <BrowserRouter>
            <Routes>
              <Route element={<AppShell />}>
                <Route index element={<HomePage />} />
                <Route path="library" element={<LibraryPage />} />
                <Route path="library/:sha" element={<LibraryDetailPage />} />
                <Route path="archive" element={<ArchivePage />} />
                <Route path="archive/:kind" element={<ArchivePage />} />
                <Route path="archive/:kind/:ident" element={<ArchivePage />} />
                <Route path="encode" element={<EncodePage />} />
                <Route path="print" element={<PrintPage />} />
                <Route path="decode" element={<DecodeSourcePage />} />
                <Route path="decode/:session" element={<DecodeSessionPage />} />
                <Route path="health" element={<HealthListPage />} />
                <Route path="health/:sha" element={<HealthDetailPage />} />
                <Route path="devices" element={<DevicesPage />} />
                <Route path="calibrate" element={<CalibratePage />} />
                <Route path="*" element={<StatusNote tone="empty" title="No such desk" detail="That route is not on the floor." />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </Tooltip.Provider>
      </ViewModeProvider>
    </QueryClientProvider>
  );
}
