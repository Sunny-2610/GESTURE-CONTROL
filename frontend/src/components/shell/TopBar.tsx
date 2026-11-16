import { NavLink } from "react-router-dom";
import { EmergencyStop } from "./EmergencyStop";

const ITEMS = [
  { index: "01", name: "Dashboard", to: "/" },
  { index: "02", name: "Tutorial", to: "/tutorial" },
  { index: "03", name: "Camera", to: "/camera" },
  { index: "04", name: "Gestures", to: "/gestures" },
  { index: "05", name: "Settings", to: "/settings" },
  { index: "06", name: "About", to: "/about" },
];

export function TopBar() {
  return (
    <header className="fixed inset-x-0 top-0 z-40 flex h-topbar items-stretch border-b border-ink bg-paper">
      <div className="flex items-center px-6 font-label uppercase tracking-[0.06em] text-ink">
        Gesture Control
      </div>
      <nav aria-label="Pages" className="flex flex-1 items-stretch justify-center">
        {ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            className={({ isActive }) =>
              `flex items-center border-b-[3px] px-4 font-label uppercase tracking-[0.06em] ${
                isActive
                  ? "border-ink text-ink"
                  : "border-transparent text-ink-muted hover:text-ink"
              }`
            }
          >
            <span className="hidden font-mono lg:inline">{item.index}</span>
            <span className="hidden lg:ml-2 lg:inline">{item.name}</span>
            <span className="lg:hidden">{item.index}</span>
          </NavLink>
        ))}
      </nav>
      <div className="flex items-center pr-3">
        <EmergencyStop />
      </div>
    </header>
  );
}
