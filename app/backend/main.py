import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.config import settings
from pages.routes import router as pages_routes
from tasks.entities import InvalidTaskError, TaskNotFoundError
from tasks.routes import router as tasks_routes
from users.routes import router as users_routes

logger = logging.getLogger("todo")

tags_metadata = [
    {
        "name": "tasks",
        "description": "Operations related to task management",
        "externalDocs": {
            "description": "More about tasks",
            "url": "https://example.com/docs/tasks",
        },
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan"""
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    title="Todo App",
    description="Simple todo app for testing purpose",
    summary="Remember everything todo...",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Sepehr Maadani",
        "url": "https://github.com/sepehrmdn77/todo",
        "email": "sepehrmaadani98@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://choosealicense.com/",
    },
)

app.include_router(tasks_routes)
app.include_router(users_routes)
app.include_router(pages_routes)


@app.post("/set-cookie", tags=["Cookie management"])
def set_cookie(response: Response):
    response.set_cookie(key="test", value="something")
    return {"message": "Cookie has been set successfully"}


@app.get("/get-cookie", tags=["Cookie management"])
def get_cookie(request: Request):
    return {"requested cookie": request.cookies.get("test")}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def error_response(
    status_code: int, detail: Any, headers: Optional[dict[str, str]] = None
) -> JSONResponse:
    """Uniform error body used by every handler: {"error", "status_code", "detail"}."""
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "status_code": status_code, "detail": detail},
        headers=headers,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return error_response(exc.status_code, exc.detail, getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.info("Validation failed for %s %s", request.method, request.url.path)
    # Drop "input"/"ctx": they can contain submitted secrets (e.g. passwords).
    errors = [
        {key: value for key, value in error.items() if key not in ("input", "ctx")}
        for error in exc.errors()
    ]
    return error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, jsonable_encoder(errors))


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError):
    return error_response(status.HTTP_404_NOT_FOUND, "Task not found")


@app.exception_handler(InvalidTaskError)
async def invalid_task_handler(request: Request, exc: InvalidTaskError):
    return error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
