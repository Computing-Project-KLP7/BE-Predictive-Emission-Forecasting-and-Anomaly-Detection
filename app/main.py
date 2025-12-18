from fastapi import FastAPI
from app.api.routes import router as api_router

app = FastAPI(title="Predictive Emission API")

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "API berjalan"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
