from fastapi import APIRouter
from app.api import activity_logs, auth, donors, health, inventory, matching, predictions, requesters, requests, staff

api_router = APIRouter(prefix="/api")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(staff.router)
api_router.include_router(activity_logs.router)
api_router.include_router(donors.router)
api_router.include_router(inventory.router)
api_router.include_router(matching.router)
api_router.include_router(requesters.router)
api_router.include_router(requests.router)
api_router.include_router(predictions.router)


