"""REST + streaming routes."""
from __future__ import annotations

import asyncio
import time
from typing import Dict

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.api.runtime import get_runtime
from app.schemas.models import (
    ArmRequest,
    CommandResponse,
    EventEntry,
    GestureRegistry,
    StatusResponse,
    WsEventMessage,
    WsFrameMessage,
    WsHand,
    WsStateMessage,
)
from app.state.machine import VERSION, InvalidTransition, now_stamp

router = APIRouter()


# --- status -----------------------------------------------------------------

@router.get("/api/status", response_model=StatusResponse)
def status(request: Request) -> StatusResponse:
    rt = get_runtime(request)
    snap = rt.machine.snapshot()
    cam = rt.pipeline.camera if rt.pipeline else None
    from app.schemas.models import CameraStatus, ControllerStatus

    camera_status = CameraStatus(
        open=bool(cam and cam.open),
        busy=bool(cam and cam.error),
        resolution=cam.resolution() if cam else None,
        fps=rt.pipeline.snapshot.fps if rt.pipeline else None,
        error=cam.error if cam else None,
    )
    controller_status = ControllerStatus(
        state=snap["state"],
        changed_at=snap["changed_at"],
        since=snap["since"],
    )
    return StatusResponse(
        version=VERSION,
        system=rt.system_info(),
        camera=camera_status,
        controller=controller_status,
        checks=rt.system_checks(),
        uptime_s=round(time.time() - rt.started_at, 1),
        fps=rt.pipeline.snapshot.fps if rt.pipeline else None,
        latency_ms=None,
    )


@router.get("/api/events", response_model=list[EventEntry])
def events(request: Request) -> list[EventEntry]:
    rt = get_runtime(request)
    return list(rt.machine.log)


# --- controller ---------------------------------------------------------------

@router.post("/api/controller/start", response_model=CommandResponse)
def controller_start(request: Request, body: ArmRequest) -> CommandResponse:
    rt = get_runtime(request)
    if not all(body.checks.model_dump().values()):
        raise HTTPException(status_code=400, detail="All three arming checks are required.")
    try:
        if rt.machine.state.value == "HALT":
            rt.machine.rearm()
        rt.machine.arm()
        rt.machine.activate()
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CommandResponse(state=rt.machine.state, detail="control active")


@router.post("/api/controller/pause", response_model=CommandResponse)
def controller_pause(request: Request) -> CommandResponse:
    rt = get_runtime(request)
    try:
        rt.machine.pause()
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CommandResponse(state=rt.machine.state, detail="control held")


@router.post("/api/controller/resume", response_model=CommandResponse)
def controller_resume(request: Request) -> CommandResponse:
    rt = get_runtime(request)
    try:
        rt.machine.resume()
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CommandResponse(state=rt.machine.state, detail="control resumed")


@router.post("/api/controller/stop", response_model=CommandResponse)
def controller_stop(request: Request) -> CommandResponse:
    rt = get_runtime(request)
    try:
        rt.machine.stop(reason="UI")
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if rt.pipeline:
        rt.pipeline.engine.reset()
    return CommandResponse(state=rt.machine.state, detail="control off")


@router.post("/api/controller/emergency-stop", response_model=CommandResponse)
def controller_emergency_stop(request: Request) -> CommandResponse:
    rt = get_runtime(request)
    rt.emergency_stop(source="UI")
    if rt.pipeline:
        rt.pipeline.engine.reset()
    return CommandResponse(state=rt.machine.state, detail="halted")


@router.post("/api/controller/rearm", response_model=CommandResponse)
def controller_rearm(request: Request) -> CommandResponse:
    rt = get_runtime(request)
    try:
        rt.machine.rearm()
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CommandResponse(state=rt.machine.state, detail="re-armed")


# --- camera / video ------------------------------------------------------------

@router.post("/api/camera/start")
def camera_start(request: Request) -> Dict:
    rt = get_runtime(request)
    if rt.pipeline is None:
        raise HTTPException(status_code=503, detail="Vision pipeline not started.")
    ok = rt.pipeline.start_camera()
    return {"open": ok, "error": rt.pipeline.camera.error}


@router.post("/api/camera/stop")
def camera_stop(request: Request) -> Dict:
    rt = get_runtime(request)
    if rt.pipeline is None:
        raise HTTPException(status_code=503, detail="Vision pipeline not started.")
    rt.pipeline.stop_camera()
    return {"open": False}


async def _mjpeg(request: Request):
    rt = get_runtime(request)
    while True:
        snap = rt.pipeline.snapshot.copy() if rt.pipeline else {"jpeg": None}
        jpeg = snap["jpeg"]
        if jpeg:
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                + str(len(jpeg)).encode()
                + b"\r\n\r\n" + jpeg + b"\r\n"
            )
        await asyncio.sleep(1.0 / 30.0)


@router.get("/api/video")
def video(request: Request) -> StreamingResponse:
    rt = get_runtime(request)
    if rt.pipeline is None or not rt.pipeline.camera.open:
        raise HTTPException(status_code=409, detail="Camera is off.")
    return StreamingResponse(
        _mjpeg(request),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# --- gestures --------------------------------------------------------------------

@router.get("/api/gestures", response_model=GestureRegistry)
def gestures(request: Request) -> GestureRegistry:
    rt = get_runtime(request)
    registry = rt.gestures_payload()
    from app.schemas.models import GestureInfo

    return GestureRegistry(gestures=[GestureInfo(**g) for g in registry])


@router.put("/api/gestures/{name}")
def gesture_toggle(request: Request, name: str, body: Dict) -> Dict:
    rt = get_runtime(request)
    patch = {"gestures": {name: bool(body.get("enabled", True))}}
    try:
        rt.settings_store.update(patch)
        rt.settings_store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"name": name, "enabled": bool(body.get("enabled", True))}


# --- settings ----------------------------------------------------------------------

@router.get("/api/settings")
def get_settings(request: Request) -> Dict:
    rt = get_runtime(request)
    return {
        "settings": rt.settings_store.current().model_dump(mode="json"),
        "saved": rt.settings_store.saved().model_dump(mode="json"),
        "unsaved": rt.settings_store.unsaved_count(),
    }


@router.put("/api/settings")
def put_settings(request: Request, body: Dict) -> Dict:
    rt = get_runtime(request)
    patch = body.get("settings", body)
    try:
        updated = rt.settings_store.update(patch)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    saved = rt.settings_store.save()
    return {
        "settings": saved.model_dump(mode="json"),
        "unsaved": rt.settings_store.unsaved_count(),
        "applied": updated.model_dump(mode="json"),
    }


@router.post("/api/settings/reset")
def reset_settings(request: Request) -> Dict:
    rt = get_runtime(request)
    rt.settings_store.reset()
    return {"settings": rt.settings_store.current().model_dump(mode="json"), "unsaved": rt.settings_store.unsaved_count()}


# --- WebSocket -------------------------------------------------------------------------

class _WsConnection:
    """Bridges hub callbacks (any thread) into the connection's asyncio loop."""

    def __init__(self, websocket: WebSocket, loop: asyncio.AbstractEventLoop) -> None:
        self.websocket = websocket
        self.loop = loop
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=64)

    def on_hub_message(self, message: Dict) -> None:
        try:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, message)
        except RuntimeError:
            pass


@router.websocket("/ws/gestures")
async def ws_gestures(websocket: WebSocket) -> None:
    rt = websocket.app.state.runtime
    await websocket.accept()
    connection = _WsConnection(websocket, asyncio.get_running_loop())
    unsubscribe = rt.hub.subscribe(connection.on_hub_message)
    disconnected = False
    try:
        while not disconnected:
            snap = (
                rt.pipeline.snapshot.copy()
                if rt.pipeline
                else {"hands": [], "fps": None, "proc_ms": None, "ts": time.time()}
            )
            frame = WsFrameMessage(
                ts=snap["ts"],
                state=rt.machine.state,
                fps=snap.get("fps"),
                proc_ms=snap.get("proc_ms"),
                hands=[WsHand(**{k: v for k, v in h.items() if k != "pinch"}) for h in snap.get("hands", [])],
            )
            await websocket.send_text(frame.model_dump_json())
            while True:
                try:
                    message = await asyncio.wait_for(connection.queue.get(), timeout=1.0 / 30.0)
                except asyncio.TimeoutError:
                    break
                if message.get("type") == "state":
                    state_msg = WsStateMessage(state=message["state"])
                    await websocket.send_text(state_msg.model_dump_json())
                elif message.get("type") == "event":
                    event_msg = WsEventMessage(entry=EventEntry(**message["entry"]))
                    await websocket.send_text(event_msg.model_dump_json())
    except (WebSocketDisconnect, RuntimeError):
        disconnected = True
    finally:
        unsubscribe()
        settings = rt.settings_store.current()
        if settings.safety.auto_disable_on_disconnect and rt.machine.state.value in ("ACTIVE", "HOLD"):
            try:
                rt.machine.stop(reason="link lost")
                rt.machine.emit("CONTROL DISABLED", "frontend disconnected")
            except InvalidTransition:
                pass
