# AI Hand Gesture Controller

Control a Windows computer with webcam hand gestures. Safety-gated: input is
dry-run by default, control must be armed through three explicit checks, and an
emergency stop (on-screen button + global `Ctrl+Alt+Shift+Q` hotkey) is always
available.

See `../Design.md` for the interface specification.

## Structure

- `backend/` — FastAPI + MediaPipe vision pipeline, controller state machine,
  input/volume services (Python 3.12, managed with uv)
- `frontend/` — React + TypeScript + Vite + Tailwind dashboard

## Run (production, single server)

```powershell
npm --prefix frontend run build        # builds frontend/dist
$env:GESTURE_PORT = '8000'             # optional; 8000 is the default
.venv\Scripts\python.exe backend\run.py
```

Open `http://127.0.0.1:8000` — the API and the dashboard are served from the
same origin.

## Run (development)

```powershell
$env:GESTURE_PORT = '8000'             # backend port (vite proxy follows it)
.venv\Scripts\python.exe backend\run.py
npm --prefix frontend run dev          # http://localhost:5173
```

## Live input mode

Mouse/volume actions are dry-run (preview) by default. Switch at runtime in
`Settings -> Safety -> Input mode -> Live` (persisted across restarts); control
must be stopped before enabling live input.

`GESTURE_LIVE` can override the saved mode at startup:

```powershell
$env:GESTURE_LIVE = '1'   # force live
$env:GESTURE_LIVE = '0'   # force preview
```

## Tests

```powershell
.venv\Scripts\python.exe -m pytest backend -q
```

## Gestures (priority 1 = highest)

| # | Pose | Action |
|---|---|---|
| 1 | Closed fist (all fingers curled, thumb tucked) | Pause - all actions stop while held |
| 2 | Pinch click (thumb tip to index tip) | One mouse click per pinch (with hysteresis + cooldown) |
| 3 | Three-finger volume (index+middle+ring up) | Media keys: hand up = louder, down = quieter |
| 4 | Two-finger scroll (index+middle in a V) | Joystick scroll: farther from the anchor scrolls faster |
| 5 | Pointer (index only) | Moves the cursor; optional dwell click |
| 6 | Open palm (all five up) | Swipe left/right for browser back/forward |

Notes:

- Volume and scrolling are **relative**: they measure hand movement from where
  the pose started (its anchor). Return to the anchor to stop.
- Volume sends `volume up` / `volume down` media keys and shows an *estimated*
  percent (starting from 50); real feedback comes from your speaker.
- The tutorial page (`/#/tutorial`) always forces preview mode and restores
  the previous input mode on exit.

## Tunable thresholds (Settings page or `backend/app/services/control_engine.py`)

| Threshold | Default | Meaning |
|---|---|---|
| Pinch join ratio | 0.30 | thumb-index distance (× palm size) that counts as a pinch |
| Click cooldown | 0.4 s | minimum time between pinch clicks |
| Dwell radius / re-arm / time | 0.015 / 0.04 / 1.0 s | hold-still click ring (off by default) |
| Scroll dead zone | 0.04 | anchor offset below which nothing scrolls |
| Scroll range / rate cap | 0.15 / 12 notches/s | offset that reaches max speed |
| Volume dead zone | 0.03 | anchor offset below which nothing happens |
| Volume range / rate cap | 0.15 / 12 keys/s | offset that reaches max speed |
| Swipe travel / window / speed | 0.25 / 0.4 s / 0.6 /s | one open-palm swipe; cooldown 1.0 s |
| Hand-lost auto-hold | 5.0 s | ACTIVE auto-holds when no hand is seen |
