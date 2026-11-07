"""
Точка входа FastAPI. Регистрирует роутеры, кастомный OpenAPI и Swagger UI.
"""

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

from app.api.chart_routes import router as chart_router
from app.openapi import custom_openapi

app = FastAPI(
    title="Crypto Alert API",          # переопределяется в openapi()
    version="1.0.0",
    # Отключаем автогенерируемые docs, чтобы подставить кастомный Swagger UI.
    docs_url=None,
    redoc_url="/redoc",                # Redoc оставляем как есть
    openapi_url="/openapi.json",
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
)

# --- Регистрация роутеров ---------------------------------------------
app.include_router(chart_router)

# --- Кастомная OpenAPI-схема ------------------------------------------
app.openapi = lambda: custom_openapi(app)  # type: ignore[method-assign]


# --- Swagger UI с настройками UX --------------------------------------
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """
    Swagger UI с включёнными удобствами:
    - persistAuthorization — токены не теряются при перезагрузке
    - filter              — поиск по эндпоинтам
    - displayRequestDuration — время выполнения запроса
    - tryItOutEnabled     — «Try it out» включён по умолчанию
    - deepLinking         — прямые ссылки на эндпоинты
    - defaultModelsExpandDepth — модели свёрнуты, но доступны
    """
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} — Swagger UI",
        swagger_ui_parameters={
            "persistAuthorization": True,
            "filter": True,
            "displayRequestDuration": True,
            "tryItOutEnabled": True,
            "deepLinking": True,
            "defaultModelsExpandDepth": 1,
            "defaultModelExpandDepth": 2,
            "docExpansion": "list",
            "syntaxHighlight.theme": "monokai",
            "tagsSorter": "alpha",
            "operationsSorter": "method",
        },
    )