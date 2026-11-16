"""Pydantic schemas shared across the API, the vision pipeline and the state machine."""
from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ControllerState(str, Enum):
    OFF = "OFF"
    ARMED = "ARMED"
    ACTIVE = "ACTIVE"
    HOLD = "HOLD"
    HALT = "HALT"


class CursorSettings(BaseModel):
    sensitivity: float = Field(default=1.5, ge=0.5, le=3.0)
    smoothing: float = Field(default=0.5, ge=0.0, le=0.95)
    active_region_margin: float = Field(default=0.08, ge=0.0, le=0.4)
    control_hand: Literal["left", "right"] = "right"


class ClickSettings(BaseModel):
    pinch_threshold: float = Field(default=0.3, ge=0.1, le=0.9)
    cooldown: float = Field(default=0.4, ge=0.1, le=2.0)
    double_click: bool = False
    dwell_enabled: bool = False
    dwell_ms: int = Field(default=1000, ge=500, le=3000)


class ScrollSettings(BaseModel):
    speed: float = Field(default=1.0, ge=0.2, le=5.0)
    dead_zone: float = Field(default=0.04, ge=0.0, le=0.1)


class VolumeSettings(BaseModel):
    sensitivity: float = Field(default=1.0, ge=0.1, le=3.0)
    smoothing: float = Field(default=0.6, ge=0.0, le=0.95)


class SwipeSettings(BaseModel):
    enabled: bool = True


class SafetySettings(BaseModel):
    emergency_hotkey: str = "ctrl+alt+shift+q"
    auto_disable_no_hand: float = Field(default=5.0, ge=0.0, le=30.0)
    auto_disable_on_disconnect: bool = True


class InputSettings(BaseModel):
    mode: Literal["preview", "live"] = "preview"


class GestureToggles(BaseModel):
    closed_fist: bool = True
    pinch_click: bool = True
    three_finger: bool = True
    two_finger_scroll: bool = True
    pointer: bool = True
    open_palm: bool = True


class AppSettings(BaseModel):
    cursor: CursorSettings = Field(default_factory=CursorSettings)
    click: ClickSettings = Field(default_factory=ClickSettings)
    scroll: ScrollSettings = Field(default_factory=ScrollSettings)
    volume: VolumeSettings = Field(default_factory=VolumeSettings)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    input: InputSettings = Field(default_factory=InputSettings)
    gestures: GestureToggles = Field(default_factory=GestureToggles)
    swipes: SwipeSettings = Field(default_factory=SwipeSettings)


class ArmChecks(BaseModel):
    hand_visible: bool = False
    nothing_unsaved: bool = False
    emergency_shortcut: bool = False


class ArmRequest(BaseModel):
    checks: ArmChecks = Field(default_factory=ArmChecks)


class CommandResponse(BaseModel):
    state: ControllerState
    detail: str = ""


class InputModeRequest(BaseModel):
    live: bool = False


class InputModeResponse(BaseModel):
    live: bool = False


class GestureInfo(BaseModel):
    name: str
    priority: int
    title: str
    pose: str
    action: str
    motion: str = ""
    enabled: bool


class GestureRegistry(BaseModel):
    gestures: List[GestureInfo]


class EventEntry(BaseModel):
    ts: str
    event: str
    detail: str = ""


class CameraStatus(BaseModel):
    open: bool
    busy: bool = False
    resolution: Optional[str] = None
    fps: Optional[float] = None
    error: Optional[str] = None


class ControllerStatus(BaseModel):
    state: ControllerState
    changed_at: Optional[float] = None
    since: Optional[str] = None


class SystemChecks(BaseModel):
    camera_access: Literal["OK", "FAIL"] = "FAIL"
    model_loaded: Literal["OK", "FAIL"] = "FAIL"
    input_backend: Literal["OK", "FAIL"] = "FAIL"
    volume_backend: Literal["OK", "FAIL"] = "FAIL"


class SystemInfo(BaseModel):
    backend: str
    vision: str
    model: str
    frontend: str
    session: str


class StatusResponse(BaseModel):
    version: str
    system: SystemInfo
    camera: CameraStatus
    controller: ControllerStatus
    checks: SystemChecks
    uptime_s: float
    fps: Optional[float] = None
    latency_ms: Optional[float] = None
    input_live: bool = False


# --- WebSocket messages -------------------------------------------------

class WsHand(BaseModel):
    hand: str
    role: Literal["primary", "secondary"]
    confidence: float
    gesture: str
    landmarks: List[List[float]]
    finger_states: List[bool]
    cursor: Optional[List[int]] = None


class EngineToast(BaseModel):
    text: str
    ts: float


class WsFrameMessage(BaseModel):
    type: Literal["frame"] = "frame"
    ts: float
    state: ControllerState
    fps: Optional[float] = None
    proc_ms: Optional[float] = None
    hands: List[WsHand] = Field(default_factory=list)
    # ControlEngine.status() feedback
    mode: str = "idle"
    volume: Optional[float] = None
    volume_direction: int = 0
    scroll_velocity: float = 0.0
    dwell_progress: float = 0.0
    volume_anchor: Optional[float] = None
    toast: Optional[EngineToast] = None


class WsStateMessage(BaseModel):
    type: Literal["state"] = "state"
    state: ControllerState


class WsEventMessage(BaseModel):
    type: Literal["event"] = "event"
    entry: EventEntry
