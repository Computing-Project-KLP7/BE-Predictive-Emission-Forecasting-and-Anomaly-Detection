from fastapi import FastAPI
from app.api.router import router as main_router
from app.api.v1.router import api_router


app = FastAPI(
    title="TransTRACK API",
    description="Predictive Emission Forecasting & Anomaly Detection",
    version="1.0.0",
)

app.include_router(main_router) # add main router for general routes
app.include_router(api_router, prefix="/api/v1")