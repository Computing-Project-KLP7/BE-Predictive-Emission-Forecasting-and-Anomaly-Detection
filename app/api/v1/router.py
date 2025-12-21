from fastapi import APIRouter
from app.api.v1 import authentication, emission, anomaly, transtrack, dashboard, notification, authentication


api_router = APIRouter()


api_router.include_router(authentication.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(transtrack.router, prefix="/transtrack", tags=["Transtrack Data Summary (Data Integration & Processing)"])
api_router.include_router(emission.router, prefix="/emission", tags=["Emission Prediction Engine"])
api_router.include_router(anomaly.router, prefix="/anomaly", tags=["Anomaly Detection Engine"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard & Visualization"])
api_router.include_router(notification.router, prefix="/notification", tags=["Notification System"])