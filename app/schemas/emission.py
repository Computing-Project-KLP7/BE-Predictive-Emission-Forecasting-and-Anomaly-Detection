from pydantic import BaseModel
from datetime import datetime


class EmissionRequest(BaseModel):
    timestamp: datetime
    device_id: int
    odometer_km: float
    fuel_level_L: float
    rpm: int
    ignition_status: bool
    movement_state: str
    battery_voltage: float


class EmissionResponse(BaseModel):
    predicted_emission: float
    unit: str = "gCO2/km"