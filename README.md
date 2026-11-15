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
| 1 | Closed fist | Rest pose — all actions stop |
| 2 | Volume mode (thumb out) | Vertical hand movement sets master volume |
| 3 | Two-finger scroll | Vertical movement scrolls |
| 4 | Pinch click | Single click per pinch |
| 5 | Pointer (index only) | Moves the cursor |
| 6 | Open palm | Neutral — nothing dispatched |
