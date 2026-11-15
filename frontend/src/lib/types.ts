export type ControllerState = "OFF" | "ARMED" | "ACTIVE" | "HOLD" | "HALT";

export interface EventEntry {
  ts: string;
  event: string;
  detail: string;
}

export interface CameraStatus {
  open: boolean;
  busy: boolean;
  resolution: string | null;
  fps: number | null;
  error: string | null;
}

export interface ControllerStatus {
  state: ControllerState;
  changed_at: number | null;
  since: string | null;
}

export interface SystemChecks {
  camera_access: "OK" | "FAIL";
  model_loaded: "OK" | "FAIL";
  input_backend: "OK" | "FAIL";
  volume_backend: "OK" | "FAIL";
}

export interface SystemInfo {
  backend: string;
  vision: string;
  model: string;
  frontend: string;
  session: string;
}

export interface Status {
  version: string;
  system: SystemInfo;
  camera: CameraStatus;
  controller: ControllerStatus;
  checks: SystemChecks;
  uptime_s: number;
  fps: number | null;
  latency_ms: number | null;
}

export interface GestureInfo {
  name: string;
  priority: number;
  title: string;
  pose: string;
  action: string;
  enabled: boolean;
}

export interface Settings {
  cursor: {
    sensitivity: number;
    smoothing: number;
    active_region_margin: number;
    control_hand: "left" | "right";
  };
  click: { pinch_threshold: number; cooldown: number; double_click: boolean };
  scroll: { speed: number; dead_zone: number };
  volume: { sensitivity: number; smoothing: number };
  safety: {
    emergency_hotkey: string;
    auto_disable_no_hand: number;
    auto_disable_on_disconnect: boolean;
  };
  gestures: Record<string, boolean>;
}

export interface Landmark extends Array<number> {}

export interface WsHand {
  hand: string;
  role: "primary" | "secondary";
  confidence: number;
  gesture: string;
  landmarks: Landmark[];
  finger_states: boolean[];
  cursor: number[] | null;
}

export interface WsFrame {
  type: "frame";
  ts: number;
  state: ControllerState;
  fps: number | null;
  proc_ms: number | null;
  hands: WsHand[];
}

export interface WsFrameMessage {
  type: "frame";
  ts: number;
  state: ControllerState;
  fps: number | null;
  proc_ms: number | null;
  hands: WsHand[];
}

export interface WsStateMessage {
  type: "state";
  state: ControllerState;
}

export interface WsEventMessage {
  type: "event";
  entry: EventEntry;
}

export type WsMessage = WsFrameMessage | WsStateMessage | WsEventMessage;

export interface SettingsPayload {
  settings: Settings;
  saved: Settings;
  unsaved: number;
}
