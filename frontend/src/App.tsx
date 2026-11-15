import { HashRouter, Route, Routes } from "react-router-dom";
import { AppProvider } from "./hooks/AppContext";
import { AppLayout } from "./pages/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { CameraPage } from "./pages/Camera";
import { GesturesPage } from "./pages/Gestures";
import { SettingsPage } from "./pages/Settings";
import { AboutPage } from "./pages/About";

export function App() {
  return (
    <AppProvider>
      <HashRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="/camera" element={<CameraPage />} />
            <Route path="/gestures" element={<GesturesPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Route>
        </Routes>
      </HashRouter>
    </AppProvider>
  );
}
