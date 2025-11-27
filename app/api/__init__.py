from fastapi import APIRouter

from . import contacts, leads, operators, sources

api_router = APIRouter()

api_router.include_router(operators.router, prefix="/operators", tags=["operators"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])


