from fastapi import APIRouter
from app.schemas.emission import EmissionRequest, EmissionResponse
# from app.services.emission_service import predict_emission


router = APIRouter()


@router.post("/predict", response_model=EmissionResponse)
def predict(data: EmissionRequest):
    # result = predict_emission(data)
    return ()