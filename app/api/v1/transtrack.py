from fastapi import APIRouter


router = APIRouter()


@router.get("/")
def data_summary(emision_id: int):
    return {"status": "healthy", "emission_id": emision_id}