from fastapi import APIRouter, HTTPException, Query
from app.schemas.notification import (
    DashboardNotificationInput,
    DashboardNotificationOutput,
    AnomalyNotificationInput,
    AnomalyNotificationOutput,
    NotificationHistoryInput,
    NotificationHistoryOutput,
    NotificationPriority,
    NotificationType
)
from app.services.notification_service import (
    generate_dashboard_notifications,
    generate_anomaly_notifications,
    get_notification_history,
    mark_notifications_as_read
)


router = APIRouter()


@router.post("/dashboard", response_model=DashboardNotificationOutput)
async def generate_dashboard_notification(data: DashboardNotificationInput):
    """
    Generate notifikasi berdasarkan dashboard metrics.
    
    Endpoint ini menganalisis metrics dashboard dan menghasilkan notifikasi untuk:
    - Fuel Theft Alert (CRITICAL)
    - Emission Intensity (CRITICAL, HIGH, MEDIUM)
    - Idle Time (CRITICAL, MEDIUM)
    - Total Emissions & Fuel Consumption
    - Performance Summary
    
    ### Notification Priorities:
    - **CRITICAL**: Memerlukan tindakan segera (fuel theft, critical idle, critical emissions)
    - **HIGH**: Memerlukan perhatian segera (high emissions, high fuel consumption)
    - **MEDIUM**: Monitor dan optimalkan
    - **LOW**: Info positif - performa optimal
    
    ### Example Request (Critical Idle):
    ```json
    {
        "device_id": 123,
        "total_emissions_kg": 15.2,
        "emission_intensity_gco2_km": 250.5,
        "idle_time_hours": 2.5,
        "status_color": "🔴 Red (Critical)",
        "total_fuel_consumed_l": 5.7,
        "total_distance_km": 60.5,
        "has_theft_alert": false
    }
    ```
    
    ### Response:
    ```json
    {
        "device_id": 123,
        "total_notifications": 2,
        "critical_count": 1,
        "high_count": 1,
        "medium_count": 0,
        "low_count": 0,
        "notifications": [...],
        "summary": "🔴 1 alert CRITICAL memerlukan tindakan segera!",
        "requires_immediate_action": true
    }
    ```
    """
    try:
        result = generate_dashboard_notifications(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomaly", response_model=AnomalyNotificationOutput)
async def generate_anomaly_notification(data: AnomalyNotificationInput):
    """
    Generate notifikasi dari anomaly detection result.
    
    Endpoint ini mengkonversi anomaly detection output menjadi user-friendly notification.
    
    ### Anomaly Types:
    - **fuel_theft**: Fuel drop > 5L saat kendaraan diam
    - **emission_inefficient**: CO2 intensity > mean + 2*std
    - **ml_detected**: Anomali terdeteksi oleh Isolation Forest
    - **excessive_idle**: Total idle > 120 menit per hari
    
    ### Example Request (Fuel Theft):
    ```json
    {
        "device_id": 123,
        "anomaly_type": "fuel_theft",
        "anomaly_score": -0.85,
        "severity": "CRITICAL",
        "confidence": 0.98,
        "details": {
            "fuel_delta": -10.5,
            "speed": 0,
            "distance_delta": 0.05
        }
    }
    ```
    
    ### Response:
    ```json
    {
        "device_id": 123,
        "timestamp": "2025-12-21T10:30:00",
        "notification_id": "uuid...",
        "notification_type": "FUEL_THEFT_ALERT",
        "title": "🚨 FUEL THEFT DETECTED",
        "message": "...",
        "priority": "CRITICAL",
        "recommended_action": "INVESTIGATE_IMMEDIATELY",
        "is_urgent": true
    }
    ```
    """
    try:
        result = generate_anomaly_notifications(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{device_id}")
async def get_notification_history_endpoint(
    device_id: int,
    limit: int = Query(50, description="Limit jumlah notifikasi", ge=1, le=1000),
    days: int = Query(7, description="Jumlah hari history", ge=1, le=90),
    notification_type: str = Query(None, description="Filter by notification type"),
    priority: str = Query(None, description="Filter by priority")
):
    """
    Get notification history untuk device.
    
    ### Query Parameters:
    - **device_id**: ID kendaraan (path parameter)
    - **limit**: Jumlah notifikasi yang diambil (default 50, max 1000)
    - **days**: Jumlah hari history (default 7, max 90)
    - **notification_type**: Filter by type (EMISSION_ALERT, FUEL_THEFT_ALERT, dll)
    - **priority**: Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)
    
    ### Example:
    ```
    GET /api/v1/notification/history/123?limit=20&days=7&priority=HIGH
    ```
    """
    try:
        history = get_notification_history(device_id, limit=limit, days=days)
        
        # Apply filters if specified
        notifications = history['notifications']
        
        if notification_type:
            notifications = [n for n in notifications if n['notification_type'] == notification_type]
        
        if priority:
            notifications = [n for n in notifications if n['priority'] == priority]
        
        history['notifications'] = notifications
        history['total_records'] = len(notifications)
        
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-as-read/{device_id}")
async def mark_as_read_endpoint(
    device_id: int,
    limit: int = Query(None, description="Limit jumlah notifikasi yang di-mark")
):
    """
    Mark notifikasi sebagai READ.
    
    ### Parameters:
    - **device_id**: ID kendaraan
    - **limit**: Limit jumlah yang di-mark (default: all)
    
    ### Example:
    ```
    POST /api/v1/notification/mark-as-read/123?limit=10
    ```
    """
    try:
        result = mark_notifications_as_read(device_id, limit=limit)
        return {
            "status": result['status'],
            "device_id": result['device_id'],
            "marked_count": result['marked_count']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thresholds")
async def get_notification_thresholds():
    """
    Get notification thresholds yang digunakan.
    
    Returns konfigurasi threshold untuk:
    - Emission Intensity (critical, high, medium)
    - Idle Time (critical, warning)
    - Fuel Consumption (high, medium)
    """
    try:
        from app.services.notification_service import NOTIFICATION_THRESHOLDS
        
        return {
            "status": "success",
            "thresholds": NOTIFICATION_THRESHOLDS,
            "description": {
                "emission_intensity_critical": "gCO2/km - Alert CRITICAL",
                "emission_intensity_high": "gCO2/km - Alert HIGH",
                "emission_intensity_medium": "gCO2/km - Alert MEDIUM",
                "idle_time_critical": "hours - Alert CRITICAL",
                "idle_time_warning": "hours - Alert MEDIUM",
                "fuel_consumption_high": "liters - Alert HIGH",
                "fuel_consumption_medium": "liters - Monitor"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))