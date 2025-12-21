from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class NotificationPriority(str, Enum):
    """Enum untuk notification priority"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationType(str, Enum):
    """Enum untuk tipe notifikasi"""
    EMISSION_ALERT = "EMISSION_ALERT"
    IDLE_TIME_ALERT = "IDLE_TIME_ALERT"
    FUEL_THEFT_ALERT = "FUEL_THEFT_ALERT"
    EMISSION_EFFICIENCY = "EMISSION_EFFICIENCY"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    MAINTENANCE_REMINDER = "MAINTENANCE_REMINDER"
    SYSTEM_INFO = "SYSTEM_INFO"


class DashboardNotificationInput(BaseModel):
    """Schema untuk generate notifikasi berdasarkan dashboard metrics"""
    device_id: int = Field(..., description="Device ID")
    total_emissions_kg: float = Field(..., description="Total emisi harian (kgCO2)", ge=0)
    emission_intensity_gco2_km: float = Field(..., description="Intensitas emisi (gCO2/km)", ge=0)
    idle_time_hours: float = Field(..., description="Total idle time (jam)", ge=0)
    status_color: str = Field(..., description="Status warna (🟢 Green/🟡 Yellow/🔴 Red)")
    total_fuel_consumed_l: float = Field(default=0, description="Total fuel consumed (liter)", ge=0)
    total_distance_km: float = Field(default=0, description="Total distance (km)", ge=0)
    has_theft_alert: bool = Field(default=False, description="Apakah ada fuel theft alert")


class NotificationDetail(BaseModel):
    """Detail dari setiap notifikasi"""
    notification_type: NotificationType = Field(..., description="Tipe notifikasi")
    title: str = Field(..., description="Judul notifikasi")
    message: str = Field(..., description="Pesan notifikasi")
    priority: NotificationPriority = Field(..., description="Priority level")
    action: str = Field(default="INFO", description="Action yang direkomendasikan")
    threshold: Optional[float] = Field(default=None, description="Threshold yang terlampaui")
    current_value: Optional[float] = Field(default=None, description="Nilai saat ini")


class DashboardNotificationOutput(BaseModel):
    """Schema untuk output notifikasi dashboard"""
    device_id: int = Field(..., description="Device ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp notifikasi")
    total_notifications: int = Field(..., description="Total jumlah notifikasi")
    critical_count: int = Field(..., description="Jumlah notifikasi CRITICAL")
    high_count: int = Field(..., description="Jumlah notifikasi HIGH")
    medium_count: int = Field(..., description="Jumlah notifikasi MEDIUM")
    low_count: int = Field(..., description="Jumlah notifikasi LOW")
    notifications: List[NotificationDetail] = Field(..., description="List detail notifikasi")
    summary: str = Field(..., description="Summary notifikasi")
    requires_immediate_action: bool = Field(..., description="Apakah perlu immediate action")


class AnomalyNotificationInput(BaseModel):
    """Schema untuk notifikasi anomaly detection"""
    device_id: int = Field(..., description="Device ID")
    anomaly_type: str = Field(..., description="Tipe anomali (fuel_theft, emission_inefficient, dll)")
    anomaly_score: float = Field(..., description="Anomaly score", ge=-1, le=1)
    severity: str = Field(..., description="Severity level (LOW, MEDIUM, HIGH, CRITICAL)")
    confidence: float = Field(..., description="Confidence score", ge=0, le=1)
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detail anomali")


class AnomalyNotificationOutput(BaseModel):
    """Schema untuk output notifikasi anomaly"""
    device_id: int = Field(..., description="Device ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")
    notification_id: str = Field(..., description="Unique notification ID")
    notification_type: NotificationType = Field(..., description="Tipe notifikasi")
    title: str = Field(..., description="Judul")
    message: str = Field(..., description="Pesan detail")
    priority: NotificationPriority = Field(..., description="Priority")
    recommended_action: str = Field(..., description="Tindakan yang direkomendasikan")
    is_urgent: bool = Field(..., description="Apakah urgent")


class NotificationHistoryInput(BaseModel):
    """Schema untuk query notification history"""
    device_id: int = Field(..., description="Device ID")
    limit: int = Field(default=50, description="Jumlah notifikasi yang diambil", ge=1, le=1000)
    notification_type: Optional[NotificationType] = Field(default=None, description="Filter by type")
    priority: Optional[NotificationPriority] = Field(default=None, description="Filter by priority")
    days: int = Field(default=7, description="Jumlah hari history", ge=1, le=90)


class NotificationRecord(BaseModel):
    """Record notifikasi untuk history"""
    timestamp: datetime
    device_id: int
    notification_type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    status: str = Field(default="UNREAD")  # UNREAD, READ, ARCHIVED


class NotificationHistoryOutput(BaseModel):
    """Schema untuk output notification history"""
    device_id: int
    total_records: int
    unread_count: int
    notifications: List[NotificationRecord]
