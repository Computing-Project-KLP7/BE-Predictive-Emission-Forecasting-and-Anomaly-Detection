from fastapi import APIRouter
from app.api.v1 import emission, anomaly, transtrack_data


api_router = APIRouter()


api_router.include_router(emission.router, prefix="/emission", tags=["Emission"])
api_router.include_router(anomaly.router, prefix="/anomaly", tags=["Anomaly"])
api_router.include_router(transtrack_data.router, prefix="/transtrack-data", tags=["Transtrack Data Summary (Data Integration & Processing)"])