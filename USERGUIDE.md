# Gesture Control — User Manual

A webcam reads your hand and turns gestures into mouse, scroll, volume and
system actions on Windows. Nothing is sent to your computer until you
explicitly arm control, and the emergency stop always works.

---

## 1. Requirements

- Windows 10/11
- Webcam (built-in or USB)
- Python 3.12 dependencies already installed in `.venv` (see README if not)
- Node.js only needed if you rebuild the frontend (`npm --prefix frontend run build`)

## 2. Starting the app

```powershell
cd ai-hand-gesture-controller
npm --prefix frontend run build     # once, or after frontend changes
.venv\Scripts\python.exe backend\run.py
```

Open **http://127.0.0.1:8000** in your browser.

> Port 8000 busy? Use another port:
> ```powershell
> $env:GESTURE_PORT = '8020'
> .venv\Scripts\python.exe backend\run.py
> ```

## 3. Trial mode vs. live mode (IMPORTANT)

By default the app runs in **dry-run**: it tracks your hand and shows
everything, but mouse/volume actions are only written to the event log —
nothing moves your cursor.

- **Dry-run (safe)** — default. Practice and tune settings here.
- **Live mode** — real cursor movement, clicks, scrolling, volume:

  ```powershell
  $env:GESTURE_LIVE = '1'
  .venv\Scripts\python.exe backend\run.py
  ```

Start in dry-run. Switch to live only when you are comfortable, sitting at the
desk, with nothing unsaved.

## 4. The screen

- **Top bar** — `01 Dashboard · 02 Camera · 03 Gestures · 04 Settings · 05 About`,
  plus the orange **EMERGENCY STOP** button (always visible, on every page).
- **Status line** (bottom) — link, camera, resolution, FPS, latency.
- **Dashboard** — the live viewfinder with your hand skeleton and the big
  CONTROL state word.

### Controller states

| State | Meaning |
|---|---|
| OFF | Tracking only. Nothing is controlled. |
| ARMED | Control is being armed (brief transitional state). |
| ACTIVE | Gestures dispatch real input. Skeleton turns orange. |
| HOLD | Paused. Nothing is dispatched; skeleton is still orange. |
| HALT | Emergency stop was pressed. Everything is blocked until you re-arm. |

## 5. Starting control (arming)

1. On the Dashboard, press **START CONTROL** (camera off? press **START CAMERA**
   in the viewfinder first).
2. A sheet opens with three checks. Confirm all three:
   - My hand is visible in the preview.
   - Nothing important is unsaved.
   - I know the emergency shortcut.
3. Press **ARM** (locked until all three are checked).

Control is now ACTIVE. To pause without disarming: **PAUSE**; resume with
**RESUME**. To end control normally: **STOP CONTROL**.

## 6. Gestures

Point your **control hand** (right by default) at the camera. Higher priority
wins; only one action happens at a time.

| Priority | Gesture (pose) | What it does |
|---|---|---|
| 1 | **Closed fist** — all fingers curled | Rest. Everything stops while held. |
| 2 | **Volume mode** — thumb out, fingers curled | Move hand up = louder, down = quieter. |
| 3 | **Two-finger scroll** — index + middle up | Move hand up/down to scroll the page. |
| 4 | **Pinch click** — thumb tip touches index tip | One mouse click per pinch. |
| 5 | **Pointer** — index finger only | Moves the cursor. |
| 6 | **Open palm** — all five fingers up | Neutral. Nothing happens. |

Tips:

- Curl the unused fingers clearly — half-extended fingers confuse the classifier.
- Make a fist or open palm to "let go" before switching gestures.
- Small, slow movements work best at first.

### Emergency stop

- Button: orange **EMERGENCY STOP** in the top bar, on every page.
- Keyboard (works even when the browser is not focused):
  **Ctrl + Alt + Shift + Q**
- Effect: state becomes HALT, all input is blocked. Press **RE-ARM** (alert
  strip or Dashboard) to return to OFF, then arm again.

### Automatic fail-safes

- Hand leaves the frame for 5 s while ACTIVE → control stops automatically.
- Browser tab/server connection lost → control stops automatically.
  (Both configurable on the Settings page.)

## 7. Pages

- **02 Camera** — inspect tracking: handedness, confidence, finger-state bars,
  landmark table, skeleton and active-region toggles, processing time.
- **03 Gestures** — the reference manual. Toggle any gesture on/off with the
  switch on its card; click a card for details. Detected gesture's cell inverts.
- **04 Settings** — cursor sensitivity/smoothing, click threshold/cooldown,
  scroll speed, volume sensitivity, safety timers. Values apply live after
  **SAVE**; changed rows get a left bar until saved.
- **05 About** — version info and a system check (camera, model, input, volume).

## 8. Recommended first session (5 minutes)

1. Run in dry-run (default), start the camera, arm control.
2. Hold up your **pointer** hand; watch `CURSOR x / y` chip move.
3. Pinch a few times — see `PINCH -> CLICK` events in the log.
4. Try two-finger scroll and volume mode.
5. Press **EMERGENCY STOP** once, then **RE-ARM**, so you know the drill.
6. Tune Settings (sensitivity, pinch threshold) to your hand.
7. Set `$env:GESTURE_LIVE='1'`, restart, and repeat briefly for real.

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| "Camera busy" | Another app (Teams/Zoom/OBS) holds the webcam. Close it, then START CAMERA. |
| No skeleton appears | Make sure the camera is started; check 02 Camera for tracking. |
| Skeleton drawn in ink, not orange | Control is not ACTIVE — that is by design. |
| Cursor jumps too much | Lower Cursor → Sensitivity or raise Smoothing. |
| Accidental clicks | Raise Click → Cooldown, or disable pinch in 03 Gestures. |
| Volume changes by itself | Volume-mode misread (thumb up). Make a fist first. |
| LINK LOST in the status line | Backend not running, or wrong port. Check the console, then RETRY. |
| Hotkey does nothing | Another app may own the shortcut. Check the event log for `HOTKEY UNAVAILABLE` and free the combo. |

## 10. Safety rules

- Never rely on gestures while standing far from the desk in live mode.
- Always leave one hand free for the keyboard shortcut.
- Save your work before arming; the dashboard warns you but cannot know everything.
- If anything feels wrong: **EMERGENCY STOP** first, ask questions after.
