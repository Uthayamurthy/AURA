import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

OFFLINE_THRESHOLD_SECONDS = 15  # Device considered offline after 15s without heartbeat


class DeviceInfo:
    def __init__(self, device_type: str, device_id: str):
        self.device_type = device_type  # "beacon" or "headcount"
        self.device_id = device_id
        self.last_seen: float = time.time()
        self.headcount: Optional[int] = None  # Only for headcount devices

    @property
    def is_online(self) -> bool:
        return (time.time() - self.last_seen) < OFFLINE_THRESHOLD_SECONDS

    def to_dict(self) -> dict:
        return {
            "type": self.device_type,
            "device_id": self.device_id,
            "status": "online" if self.is_online else "offline",
            "last_seen": self.last_seen,
            "headcount": self.headcount,
        }


class DeviceTracker:
    def __init__(self):
        self.devices: dict[str, DeviceInfo] = {}  # key: "{type}:{device_id}"

    def heartbeat(self, device_type: str, device_id: str):
        key = f"{device_type}:{device_id}"
        if key not in self.devices:
            self.devices[key] = DeviceInfo(device_type, device_id)
            logger.info(f"New device registered: {key}")
        self.devices[key].last_seen = time.time()

    def update_headcount(self, room_id: str, value: int):
        key = f"headcount:{room_id}"
        if key not in self.devices:
            self.devices[key] = DeviceInfo("headcount", room_id)
        self.devices[key].headcount = value
        self.devices[key].last_seen = time.time()

    def get_all_devices(self) -> list[dict]:
        return [device.to_dict() for device in self.devices.values()]


tracker = DeviceTracker()
