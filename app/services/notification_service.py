import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.schemas.notification import (
    DashboardNotificationInput,
    DashboardNotificationOutput,
    NotificationDetail,
    NotificationPriority,
    NotificationType,
    AnomalyNotificationInput,
    AnomalyNotificationOutput
)

# In-memory notification history (for demo, can be replaced with database)
_notification_history: Dict[int, List[Dict[str, Any]]] = {}

# Thresholds untuk notification
NOTIFICATION_THRESHOLDS = {
    'emission_intensity_critical': 400,      # gCO2/km
    'emission_intensity_high': 300,          # gCO2/km
    'emission_intensity_medium': 200,        # gCO2/km
    'idle_time_critical': 2.0,               # hours
    'idle_time_warning': 0.5,                # hours
    'fuel_consumption_high': 50,             # liters
    'fuel_consumption_medium': 30,           # liters
}


def generate_dashboard_notifications(input_data: DashboardNotificationInput) -> DashboardNotificationOutput:
    """
    Generate notifikasi berdasarkan dashboard metrics
    
    Args:
        input_data: Dashboard metrics
        
    Returns:
        DashboardNotificationOutput dengan list notifikasi
    """
    notifications: List[NotificationDetail] = []
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    
    # 1. Check Fuel Theft Alert
    if input_data.has_theft_alert:
        notification = NotificationDetail(
            notification_type=NotificationType.FUEL_THEFT_ALERT,
            title="🚨 FUEL THEFT ALERT",
            message=f"Fuel theft terdeteksi pada kendaraan {input_data.device_id}. Tindakan segera diperlukan.",
            priority=NotificationPriority.CRITICAL,
            action="INVESTIGATE_IMMEDIATELY",
            threshold=0,
            current_value=0
        )
        notifications.append(notification)
        critical_count += 1
    
    # 2. Check Emission Intensity
    if input_data.emission_intensity_gco2_km > NOTIFICATION_THRESHOLDS['emission_intensity_critical']:
        notification = NotificationDetail(
            notification_type=NotificationType.EMISSION_ALERT,
            title="🔴 CRITICAL EMISSION INTENSITY",
            message=f"Intensitas emisi sangat tinggi: {input_data.emission_intensity_gco2_km:.2f} gCO2/km. "
                   f"Melebihi threshold {NOTIFICATION_THRESHOLDS['emission_intensity_critical']} gCO2/km. "
                   f"Lakukan pemeriksaan mesin segera.",
            priority=NotificationPriority.CRITICAL,
            action="PERFORM_ENGINE_CHECK",
            threshold=NOTIFICATION_THRESHOLDS['emission_intensity_critical'],
            current_value=input_data.emission_intensity_gco2_km
        )
        notifications.append(notification)
        critical_count += 1
    elif input_data.emission_intensity_gco2_km > NOTIFICATION_THRESHOLDS['emission_intensity_high']:
        notification = NotificationDetail(
            notification_type=NotificationType.EMISSION_ALERT,
            title="⚠️ HIGH EMISSION INTENSITY",
            message=f"Intensitas emisi tinggi: {input_data.emission_intensity_gco2_km:.2f} gCO2/km. "
                   f"Pertimbangkan untuk melakukan maintenance mesin.",
            priority=NotificationPriority.HIGH,
            action="MONITOR_AND_SCHEDULE_MAINTENANCE",
            threshold=NOTIFICATION_THRESHOLDS['emission_intensity_high'],
            current_value=input_data.emission_intensity_gco2_km
        )
        notifications.append(notification)
        high_count += 1
    elif input_data.emission_intensity_gco2_km > NOTIFICATION_THRESHOLDS['emission_intensity_medium']:
        notification = NotificationDetail(
            notification_type=NotificationType.EMISSION_EFFICIENCY,
            title="💡 MODERATE EMISSION LEVELS",
            message=f"Intensitas emisi: {input_data.emission_intensity_gco2_km:.2f} gCO2/km. "
                   f"Monitor pola penggunaan dan pertimbangkan optimisasi gaya mengemudi.",
            priority=NotificationPriority.MEDIUM,
            action="OPTIMIZE_DRIVING_BEHAVIOR",
            threshold=NOTIFICATION_THRESHOLDS['emission_intensity_medium'],
            current_value=input_data.emission_intensity_gco2_km
        )
        notifications.append(notification)
        medium_count += 1
    
    # 3. Check Idle Time
    if input_data.idle_time_hours > NOTIFICATION_THRESHOLDS['idle_time_critical']:
        notification = NotificationDetail(
            notification_type=NotificationType.IDLE_TIME_ALERT,
            title="🔴 CRITICAL IDLE TIME",
            message=f"Waktu idle sangat tinggi: {input_data.idle_time_hours:.1f} jam. "
                   f"Melebihi threshold {NOTIFICATION_THRESHOLDS['idle_time_critical']} jam. "
                   f"Kurangi idle time untuk efisiensi bahan bakar.",
            priority=NotificationPriority.CRITICAL,
            action="REDUCE_IDLE_TIME",
            threshold=NOTIFICATION_THRESHOLDS['idle_time_critical'],
            current_value=input_data.idle_time_hours
        )
        notifications.append(notification)
        critical_count += 1
    elif input_data.idle_time_hours > NOTIFICATION_THRESHOLDS['idle_time_warning']:
        notification = NotificationDetail(
            notification_type=NotificationType.IDLE_TIME_ALERT,
            title="⚠️ HIGH IDLE TIME",
            message=f"Waktu idle tinggi: {input_data.idle_time_hours:.1f} jam. "
                   f"Usahakan untuk meminimalkan idle time.",
            priority=NotificationPriority.MEDIUM,
            action="MONITOR_IDLE_TIME",
            threshold=NOTIFICATION_THRESHOLDS['idle_time_warning'],
            current_value=input_data.idle_time_hours
        )
        notifications.append(notification)
        medium_count += 1
    
    # 4. Check Total Emissions
    if input_data.total_emissions_kg > 100:
        notification = NotificationDetail(
            notification_type=NotificationType.EMISSION_ALERT,
            title="⚠️ HIGH TOTAL EMISSIONS",
            message=f"Total emisi harian: {input_data.total_emissions_kg:.2f} kgCO2. "
                   f"Berdasarkan {input_data.total_fuel_consumed_l:.2f} liter konsumsi BBM.",
            priority=NotificationPriority.HIGH,
            action="TRACK_EMISSIONS",
            threshold=100,
            current_value=input_data.total_emissions_kg
        )
        notifications.append(notification)
        high_count += 1
    
    # 5. Check Fuel Consumption
    if input_data.total_fuel_consumed_l > NOTIFICATION_THRESHOLDS['fuel_consumption_high']:
        notification = NotificationDetail(
            notification_type=NotificationType.EMISSION_EFFICIENCY,
            title="⚠️ HIGH FUEL CONSUMPTION",
            message=f"Konsumsi bahan bakar tinggi: {input_data.total_fuel_consumed_l:.2f} liter. "
                   f"Monitor dan optimalkan penggunaan kendaraan.",
            priority=NotificationPriority.HIGH,
            action="OPTIMIZE_FUEL_CONSUMPTION",
            threshold=NOTIFICATION_THRESHOLDS['fuel_consumption_high'],
            current_value=input_data.total_fuel_consumed_l
        )
        notifications.append(notification)
        high_count += 1
    
    # 6. Positive notification - Green status
    if "🟢" in input_data.status_color and not notifications:
        notification = NotificationDetail(
            notification_type=NotificationType.SYSTEM_INFO,
            title="✅ EXCELLENT PERFORMANCE",
            message=f"Semua metrik dalam kondisi baik! Jarak tempuh: {input_data.total_distance_km:.1f} km. "
                   f"Emisi: {input_data.total_emissions_kg:.2f} kgCO2.",
            priority=NotificationPriority.LOW,
            action="CONTINUE_MONITORING",
            threshold=None,
            current_value=None
        )
        notifications.append(notification)
        low_count += 1
    
    # Determine if requires immediate action
    requires_immediate_action = critical_count > 0 or (high_count > 1)
    
    # Generate summary
    summary = _generate_notification_summary(
        critical_count, high_count, medium_count, low_count, input_data.status_color
    )
    
    # Save to history
    _save_notification_to_history(
        device_id=input_data.device_id,
        notifications=notifications
    )
    
    return DashboardNotificationOutput(
        device_id=input_data.device_id,
        total_notifications=len(notifications),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        notifications=notifications,
        summary=summary,
        requires_immediate_action=requires_immediate_action
    )


def generate_anomaly_notifications(input_data: AnomalyNotificationInput) -> AnomalyNotificationOutput:
    """
    Generate notifikasi dari anomaly detection
    
    Args:
        input_data: Anomaly detection result
        
    Returns:
        AnomalyNotificationOutput
    """
    notification_id = str(uuid.uuid4())
    
    # Map anomaly type to notification type
    anomaly_type_map = {
        'fuel_theft': NotificationType.FUEL_THEFT_ALERT,
        'emission_inefficient': NotificationType.EMISSION_ALERT,
        'ml_detected': NotificationType.ANOMALY_DETECTED,
        'excessive_idle': NotificationType.IDLE_TIME_ALERT
    }
    
    notification_type = anomaly_type_map.get(
        input_data.anomaly_type,
        NotificationType.ANOMALY_DETECTED
    )
    
    # Map severity to priority
    priority_map = {
        'CRITICAL': NotificationPriority.CRITICAL,
        'HIGH': NotificationPriority.HIGH,
        'MEDIUM': NotificationPriority.MEDIUM,
        'LOW': NotificationPriority.LOW
    }
    
    priority = priority_map.get(input_data.severity, NotificationPriority.MEDIUM)
    
    # Generate title and message based on anomaly type
    title_map = {
        'fuel_theft': '🚨 FUEL THEFT DETECTED',
        'emission_inefficient': '⚠️ EMISSION INEFFICIENCY',
        'ml_detected': '🔔 ANOMALY DETECTED',
        'excessive_idle': '⏱️ EXCESSIVE IDLE TIME'
    }
    
    title = title_map.get(input_data.anomaly_type, 'ANOMALY ALERT')
    
    # Generate detailed message
    message = _generate_anomaly_message(input_data)
    
    # Determine action
    action_map = {
        'fuel_theft': 'INVESTIGATE_IMMEDIATELY',
        'emission_inefficient': 'PERFORM_ENGINE_CHECK',
        'ml_detected': 'REVIEW_VEHICLE_STATUS',
        'excessive_idle': 'REDUCE_IDLE_TIME'
    }
    
    recommended_action = action_map.get(input_data.anomaly_type, 'INVESTIGATE')
    
    # Determine if urgent
    is_urgent = input_data.severity in ['CRITICAL', 'HIGH']
    
    # Save to history
    notification_detail = NotificationDetail(
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        action=recommended_action
    )
    
    _save_notification_to_history(
        device_id=input_data.device_id,
        notifications=[notification_detail]
    )
    
    return AnomalyNotificationOutput(
        device_id=input_data.device_id,
        notification_id=notification_id,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        recommended_action=recommended_action,
        is_urgent=is_urgent
    )


def _generate_notification_summary(
    critical: int, high: int, medium: int, low: int, status_color: str
) -> str:
    """Generate summary text untuk notifikasi"""
    if critical > 0:
        return f"🔴 {critical} alert CRITICAL memerlukan tindakan segera!"
    elif high > 0:
        return f"⚠️ {high} alert HIGH memerlukan perhatian segera."
    elif medium > 0:
        return f"💡 {medium} alert MEDIUM - monitor dan optimalkan performa."
    elif low > 0:
        return f"ℹ️ {low} info - performa kendaraan optimal, lanjutkan monitoring."
    else:
        return "✅ Tidak ada notifikasi - semua dalam kondisi baik."


def _generate_anomaly_message(input_data: AnomalyNotificationInput) -> str:
    """Generate detailed message untuk anomaly notification"""
    base_msg = f"Anomali terdeteksi: {input_data.anomaly_type.replace('_', ' ').title()}"
    base_msg += f"\nSeverity: {input_data.severity}"
    base_msg += f"\nConfidence: {input_data.confidence * 100:.1f}%"
    base_msg += f"\nAnomaly Score: {input_data.anomaly_score:.4f}"
    
    if input_data.details:
        base_msg += "\n\nDetail:"
        for key, value in input_data.details.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    base_msg += f"\n  - {k}: {v}"
            else:
                base_msg += f"\n  - {key}: {value}"
    
    return base_msg


def _save_notification_to_history(device_id: int, notifications: List[NotificationDetail]) -> None:
    """Save notifikasi ke history"""
    if device_id not in _notification_history:
        _notification_history[device_id] = []
    
    for notification in notifications:
        record = {
            'timestamp': datetime.now(),
            'notification_type': notification.notification_type.value,
            'title': notification.title,
            'message': notification.message,
            'priority': notification.priority.value,
            'status': 'UNREAD'
        }
        _notification_history[device_id].append(record)


def get_notification_history(device_id: int, limit: int = 50, days: int = 7) -> Dict[str, Any]:
    """
    Get notification history untuk device
    
    Args:
        device_id: Device ID
        limit: Jumlah records yang diambil
        days: Jumlah hari history
        
    Returns:
        Dict dengan notification history
    """
    if device_id not in _notification_history:
        return {
            'device_id': device_id,
            'total_records': 0,
            'unread_count': 0,
            'notifications': []
        }
    
    # Filter by date
    cutoff_date = datetime.now() - timedelta(days=days)
    
    history = [
        n for n in _notification_history[device_id]
        if n['timestamp'] >= cutoff_date
    ]
    
    # Sort by timestamp descending
    history = sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    # Apply limit
    history = history[:limit]
    
    # Count unread
    unread_count = sum(1 for n in history if n['status'] == 'UNREAD')
    
    return {
        'device_id': device_id,
        'total_records': len(history),
        'unread_count': unread_count,
        'notifications': history
    }


def mark_notifications_as_read(device_id: int, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Mark notifikasi sebagai READ
    
    Args:
        device_id: Device ID
        limit: Jumlah notifikasi yang di-mark (None = all)
        
    Returns:
        Result dict
    """
    if device_id not in _notification_history:
        return {'status': 'success', 'marked_count': 0}
    
    marked_count = 0
    for i, notification in enumerate(_notification_history[device_id]):
        if limit and marked_count >= limit:
            break
        
        if notification['status'] == 'UNREAD':
            notification['status'] = 'READ'
            marked_count += 1
    
    return {'status': 'success', 'marked_count': marked_count, 'device_id': device_id}
