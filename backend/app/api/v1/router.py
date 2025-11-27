from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_directories,
    admin_orders,
    admin_users,
    auth,
    client_chats,
    client_orders,
    executor_calendar,
    executor_orders,
    public,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(public.router)
api_router.include_router(client_chats.router)
api_router.include_router(client_orders.router)
api_router.include_router(executor_orders.router)
api_router.include_router(executor_calendar.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_orders.router)
api_router.include_router(admin_directories.router)
