"""
Python Integration Examples untuk Emission Prediction dan Anomaly Detection APIs
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your production URL
API_V1_ENDPOINT = f"{BASE_URL}/api/v1"

# ============================================================================
# EMISSION PREDICTION ENDPOINT EXAMPLES
# ============================================================================

class EmissionPredictionClient:
    """Client untuk Emission Prediction API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.endpoint = f"{base_url}/api/v1/emission/predict-hourly"
    
    def predict_normal_driving(self) -> Dict[str, Any]:
        """Prediksi emisi untuk normal driving scenario"""
        payload = {
            "speed_mean": 60.0,
            "speed_max": 90.0,
            "speed_std": 15.5,
            "distance_delta_total": 45.2,
            "rpm_mean": 1800.0,
            "rpm_max": 2200.0,
            "engine_load_mean": 50.0,
            "is_moving_mean": 0.85,
            "is_idle_total": 5,
            "hour": 14,
            "day_of_week": 3,
            "is_weekend": 0
        }
        
        response = requests.post(self.endpoint, json=payload)
        return response.json()
    
    def predict_city_traffic(self) -> Dict[str, Any]:
        """Prediksi emisi untuk city traffic dengan banyak idle"""
        payload = {
            "speed_mean": 25.0,
            "speed_max": 60.0,
            "speed_std": 20.0,
            "distance_delta_total": 12.5,
            "rpm_mean": 1200.0,
            "rpm_max": 2000.0,
            "engine_load_mean": 35.0,
            "is_moving_mean": 0.40,
            "is_idle_total": 30,
            "hour": 18,
            "day_of_week": 4,
            "is_weekend": 0
        }
        
        response = requests.post(self.endpoint, json=payload)
        return response.json()
    
    def predict_high_speed(self) -> Dict[str, Any]:
        """Prediksi emisi untuk high-speed driving"""
        payload = {
            "speed_mean": 100.0,
            "speed_max": 130.0,
            "speed_std": 10.0,
            "distance_delta_total": 95.0,
            "rpm_mean": 2500.0,
            "rpm_max": 3000.0,
            "engine_load_mean": 75.0,
            "is_moving_mean": 0.95,
            "is_idle_total": 2,
            "hour": 10,
            "day_of_week": 5,
            "is_weekend": 0
        }
        
        response = requests.post(self.endpoint, json=payload)
        return response.json()
    
    def predict_weekend_driving(self) -> Dict[str, Any]:
        """Prediksi emisi untuk weekend leisure driving"""
        payload = {
            "speed_mean": 55.0,
            "speed_max": 80.0,
            "speed_std": 12.0,
            "distance_delta_total": 65.0,
            "rpm_mean": 1700.0,
            "rpm_max": 2100.0,
            "engine_load_mean": 45.0,
            "is_moving_mean": 0.80,
            "is_idle_total": 8,
            "hour": 15,
            "day_of_week": 6,
            "is_weekend": 1
        }
        
        response = requests.post(self.endpoint, json=payload)
        return response.json()


# ============================================================================
# ANOMALY DETECTION ENDPOINT EXAMPLES
# ============================================================================

class AnomalyDetectionClient:
    """Client untuk Anomaly Detection API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.detect_endpoint = f"{base_url}/api/v1/anomaly/detect"
        self.daily_report_endpoint = f"{base_url}/api/v1/anomaly/daily-report"
    
    def detect_fuel_theft(self) -> Dict[str, Any]:
        """Deteksi fuel theft anomaly"""
        payload = {
            "speed": 0,
            "distance_delta": 0,
            "fuel_delta": -10.0,
            "fuel_consumption_rate": 0,
            "idle_duration": 5,
            "rpm": 0,
            "engine_load": 0,
            "co2_intensity": 0
        }
        
        response = requests.post(self.detect_endpoint, json=payload)
        return response.json()
    
    def detect_normal_operation(self) -> Dict[str, Any]:
        """Deteksi normal driving (no anomaly)"""
        payload = {
            "speed": 60.0,
            "distance_delta": 1.2,
            "fuel_delta": -0.3,
            "fuel_consumption_rate": 0.25,
            "idle_duration": 0,
            "rpm": 1800,
            "engine_load": 50.0,
            "co2_intensity": 42.5
        }
        
        response = requests.post(self.detect_endpoint, json=payload)
        return response.json()
    
    def detect_high_emission(self) -> Dict[str, Any]:
        """Deteksi high emission anomaly"""
        payload = {
            "speed": 50.0,
            "distance_delta": 0.8,
            "fuel_delta": -0.6,
            "fuel_consumption_rate": 0.75,
            "idle_duration": 1,
            "rpm": 2000,
            "engine_load": 70.0,
            "co2_intensity": 150.0
        }
        
        response = requests.post(self.detect_endpoint, json=payload)
        return response.json()
    
    def detect_excessive_fuel_consumption(self) -> Dict[str, Any]:
        """Deteksi excessive fuel consumption"""
        payload = {
            "speed": 80.0,
            "distance_delta": 2.0,
            "fuel_delta": -1.5,
            "fuel_consumption_rate": 0.75,
            "idle_duration": 0,
            "rpm": 2500,
            "engine_load": 75.0,
            "co2_intensity": 85.0
        }
        
        response = requests.post(self.detect_endpoint, json=payload)
        return response.json()
    
    def detect_excessive_idling(self) -> Dict[str, Any]:
        """Deteksi excessive idling"""
        payload = {
            "speed": 0,
            "distance_delta": 0.05,
            "fuel_delta": -0.2,
            "fuel_consumption_rate": 0,
            "idle_duration": 15,
            "rpm": 800,
            "engine_load": 15.0,
            "co2_intensity": 5.0
        }
        
        response = requests.post(self.detect_endpoint, json=payload)
        return response.json()
    
    def daily_anomaly_report(self, device_id: str, report_date: str) -> Dict[str, Any]:
        """Generate daily anomaly report untuk excessive idle detection"""
        payload = {
            "total_idle_minutes": 240,
            "total_distance_km": 125.5,
            "total_fuel_consumed_liters": 8.3,
            "average_co2_intensity": 55.2,
            "max_co2_intensity": 180.0,
            "total_harsh_accelerations": 3,
            "total_harsh_brakes": 2,
            "device_id": device_id,
            "report_date": report_date
        }
        
        response = requests.post(self.daily_report_endpoint, json=payload)
        return response.json()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def main():
    """Run all examples"""
    
    print("=" * 80)
    print("EMISSION PREDICTION EXAMPLES")
    print("=" * 80)
    
    emission_client = EmissionPredictionClient()
    
    # Example 1: Normal driving
    print("\n1. Normal Driving Scenario:")
    result = emission_client.predict_normal_driving()
    print(json.dumps(result, indent=2))
    
    # Example 2: City traffic
    print("\n2. City Traffic Scenario:")
    result = emission_client.predict_city_traffic()
    print(json.dumps(result, indent=2))
    
    # Example 3: High-speed driving
    print("\n3. High-Speed Driving Scenario:")
    result = emission_client.predict_high_speed()
    print(json.dumps(result, indent=2))
    
    # Example 4: Weekend leisure
    print("\n4. Weekend Leisure Driving:")
    result = emission_client.predict_weekend_driving()
    print(json.dumps(result, indent=2))
    
    print("\n" + "=" * 80)
    print("ANOMALY DETECTION EXAMPLES")
    print("=" * 80)
    
    anomaly_client = AnomalyDetectionClient()
    
    # Example 1: Fuel theft
    print("\n1. Fuel Theft Detection:")
    result = anomaly_client.detect_fuel_theft()
    print(json.dumps(result, indent=2))
    
    # Example 2: Normal operation
    print("\n2. Normal Operation (No Anomaly):")
    result = anomaly_client.detect_normal_operation()
    print(json.dumps(result, indent=2))
    
    # Example 3: High emission
    print("\n3. High Emission Detection:")
    result = anomaly_client.detect_high_emission()
    print(json.dumps(result, indent=2))
    
    # Example 4: Excessive fuel consumption
    print("\n4. Excessive Fuel Consumption:")
    result = anomaly_client.detect_excessive_fuel_consumption()
    print(json.dumps(result, indent=2))
    
    # Example 5: Excessive idling
    print("\n5. Excessive Idling Detection:")
    result = anomaly_client.detect_excessive_idling()
    print(json.dumps(result, indent=2))
    
    # Example 6: Daily anomaly report
    print("\n6. Daily Anomaly Report:")
    result = anomaly_client.daily_anomaly_report(
        device_id="VHCL001",
        report_date=datetime.now().strftime("%Y-%m-%d")
    )
    print(json.dumps(result, indent=2))


# ============================================================================
# INTEGRATION PATTERNS
# ============================================================================

def batch_emission_predictions(records: list) -> list:
    """
    Batch emission predictions untuk multiple hourly records
    
    Args:
        records: List of dictionaries dengan 12 emission features
    
    Returns:
        List of prediction results
    """
    client = EmissionPredictionClient()
    results = []
    
    for record in records:
        try:
            response = requests.post(client.endpoint, json=record)
            results.append({
                "status": "success",
                "data": response.json()
            })
        except Exception as e:
            results.append({
                "status": "error",
                "error": str(e)
            })
    
    return results


def batch_anomaly_detection(records: list) -> list:
    """
    Batch anomaly detection untuk multiple driving records
    
    Args:
        records: List of dictionaries dengan 8 anomaly features
    
    Returns:
        List of detection results
    """
    client = AnomalyDetectionClient()
    results = []
    
    for record in records:
        try:
            response = requests.post(client.detect_endpoint, json=record)
            results.append({
                "status": "success",
                "data": response.json()
            })
        except Exception as e:
            results.append({
                "status": "error",
                "error": str(e)
            })
    
    return results


def monitor_vehicle_health(device_id: str, records: list) -> Dict[str, Any]:
    """
    Comprehensive vehicle health monitoring combining emission and anomaly detection
    
    Args:
        device_id: Vehicle ID
        records: List of driving records
    
    Returns:
        Summary of emission and anomaly detections
    """
    emission_results = batch_emission_predictions(records)
    anomaly_results = batch_anomaly_detection(records)
    
    # Calculate statistics
    total_emissions = sum([r["data"]["co2_grams_total"] 
                          for r in emission_results 
                          if r["status"] == "success"])
    
    anomalies_detected = sum([1 
                             for r in anomaly_results 
                             if r["status"] == "success" and r["data"]["is_anomaly"]])
    
    return {
        "device_id": device_id,
        "total_records": len(records),
        "total_emissions_grams": total_emissions,
        "anomalies_detected": anomalies_detected,
        "anomaly_rate": anomalies_detected / len(records) if records else 0,
        "emission_results": emission_results,
        "anomaly_results": anomaly_results
    }


if __name__ == "__main__":
    main()
