from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "checking...",
            "redis": "checking...",
            "qdrant": "checking..."
        }
    }
