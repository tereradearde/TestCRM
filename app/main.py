from __future__ import annotations

from fastapi import FastAPI

from .api import api_router
from .database import Base, engine


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="Мини CRM: распределение лидов",
        version="0.1.0",
        description="Сервис распределяет обращения лидов между операторами с учетом весов и лимитов нагрузки.",
    )
    app.include_router(api_router)
    return app


app = create_app()


