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

By default the app runs in **dry-run (preview)**: it tracks your hand and shows
everything, but mouse/volume actions are only written to the event log —
nothing moves your cursor.

- **Preview (safe)** — default. Practice and tune settings here.
- **Live mode** — real cursor movement, clicks, scrolling, volume. Select
  `Settings -> Safety -> Input mode -> Preview | Live`. The choice is saved and
  survives restarts. Stop control before switching to Live.

The viewfinder bottom-right chip shows the actual mode (`INPUT LIVE` /
`INPUT DRY RUN`); the top-right chip shows control state (`LIVE`,
`PREVIEW ONLY`, `INPUT BLOCKED`).

Start in preview. Switch to live only when you are comfortable, sitting at the
desk, with nothing unsaved.

## 4. The screen

- **Top bar** — `01 Dashboard · 02 Tutorial · 03 Camera · 04 Gestures · 05 Settings · 06 About`,
  plus the orange **EMERGENCY STOP** button (always visible, on every page).
- **Status line** (bottom) — link, camera, resolution, FPS, latency.
- **Dashboard** — the live viewfinder with your hand skeleton and the big
  CONTROL state word. Hold an **open palm** for 2 s to open the gesture
  cheat-sheet overlay (any other gesture or `Esc` closes it).

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
| 1 | **Closed fist** — all four fingers curled, thumb tucked | Pause. Everything stops while held. |
| 2 | **Pinch click** — thumb tip touches index tip | One mouse click per pinch. |
| 3 | **Three-finger volume** — index + middle + ring up, pinky curled | Media keys: hand up = louder, down = quieter. A vertical bar with your start position appears in the viewfinder. |
| 4 | **Two-finger scroll** — index + middle up in a V | Joystick scroll: move up/down from where you started; farther scrolls faster. An arrow in the viewfinder shows direction and speed. |
| 5 | **Pointer** — index finger only | Moves the cursor. Optional dwell-click: hold the cursor still (Settings -> Click -> Dwell) and a ring fills around your fingertip, then clicks. |
| 6 | **Open palm** — all five fingers up | Swipe left/right for browser back / forward. One swipe per motion. |

While control is ACTIVE, the viewfinder shows a large mode chip (`CURSOR`,
`CLICK`, `SCROLL`, `VOLUME 42%`, `SWIPE`, `PAUSED`) and short action toasts
("Click", "Back", "Forward", "Volume 42%", "Paused") fade after about a second.

Tips:

- Curl the unused fingers clearly — half-extended fingers confuse the classifier.
- The thumb is ignored for pose classification (only its pinch distance counts),
  so a relaxed thumb will not change the gesture.
- Make a fist or open palm to "let go" before switching gestures.
- Small, slow movements work best at first.
- The pinch threshold is a fraction of your palm size, so it keeps working when
  you move closer to or further from the camera.
- Scroll and volume measure how far your hand moves **from where the pose
  started** — return to the start position to stop scrolling/changing volume.

### Emergency stop

- Button: orange **EMERGENCY STOP** in the top bar, on every page.
- Keyboard (works even when the browser is not focused):
  **Ctrl + Alt + Shift + Q**
- Effect: state becomes HALT, all input is blocked. Press **RE-ARM** (alert
  strip or Dashboard) to return to OFF, then arm again.

### Automatic fail-safes

- Hand leaves the frame for 5 s while ACTIVE → control holds automatically and
  resumes on its own as soon as a hand is back in frame.
- Browser tab/server connection lost → control stops automatically.
  (Both configurable on the Settings page.)

## 7. Pages

- **02 Tutorial** — a six-step guided practice run. It always forces preview
  mode (nothing is ever dispatched) and restores your previous input mode when
  you leave, even if you close the tab. Each step advances when you hold the
  pose for half a second; a Skip button finishes early.
- **03 Camera** — inspect tracking: handedness, confidence, finger-state bars,
  landmark table, skeleton and active-region toggles, processing time.
- **04 Gestures** — the reference manual. Toggle any gesture on/off with the
  switch on its card; click a card for a large drawing and a 3-step how-to.
  Detected gesture's cell inverts.
- **05 Settings** — cursor sensitivity/smoothing, click threshold/cooldown and
  dwell click, scroll speed/dead zone, volume sensitivity, swipe on/off, safety
  timers. Values apply live after **SAVE**; changed rows get a left bar until
  saved.
- **06 About** — version info and a system check (camera, model, input, volume).

## 8. Recommended first session (5 minutes)

1. Open **02 Tutorial** and run through the six steps — it is always preview
   only, so you can practice freely.
2. Run in dry-run (default), start the camera, arm control.
3. Hold up your **pointer** hand; watch `CURSOR x / y` chip move.
4. Pinch a few times — see `PINCH -> CLICK` events and the "Click" toast.
5. Try two-finger scroll and volume mode; watch the bar and arrow feedback.
6. Swipe with an open palm; check `SWIPE RIGHT/LEFT` events.
7. Press **EMERGENCY STOP** once, then **RE-ARM**, so you know the drill.
8. Tune Settings (sensitivity, pinch threshold) to your hand.
9. Set `Settings -> Safety -> Input mode -> Live` and repeat briefly for real.

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| "Camera busy" | Another app (Teams/Zoom/OBS) holds the webcam. Close it, then START CAMERA. |
| No skeleton appears | Make sure the camera is started; check 03 Camera for tracking. |
| Skeleton drawn in ink, not orange | Control is not ACTIVE — that is by design. |
| Cursor jumps too much | Lower Cursor → Sensitivity or raise Smoothing. |
| Accidental clicks | Raise Click → Cooldown or Pinch threshold, or disable pinch in 04 Gestures. |
| Scroll goes the wrong way / never stops | Return your hand to the pose's start position; raise Scroll → Dead zone in Settings. |
| Volume changes by itself | Make a fist first, then re-enter volume mode from a calm start position. |
| Swipes fire too easily | Disable swipes in Settings, or swipe more decisively (25% of frame width within 0.4 s). |
| Dwell ring never fills | Enable Click → Dwell in Settings, or reduce the dwell time. |
| Volume never changes | Check 06 About: the volume check must be OK. Volume uses media keys; some keyboards/apps intercept them. |
| LINK LOST in the status line | Backend not running, or wrong port. Check the console, then RETRY. |
| Hotkey does nothing | Another app may own the shortcut. Check the event log for `HOTKEY UNAVAILABLE` and free the combo. |

## 10. Safety rules

- Never rely on gestures while standing far from the desk in live mode.
- Always leave one hand free for the keyboard shortcut.
- Save your work before arming; the dashboard warns you but cannot know everything.
- If anything feels wrong: **EMERGENCY STOP** first, ask questions after.
