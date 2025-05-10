from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, Request, HTTPException, status

from fastapi.exceptions import RequestValidationError

from fastapi.responses import JSONResponse

from starlette.exceptions import HTTPException as StarletteHTTPException


from fastapi.middleware.cors import CORSMiddleware

from tasks.routes import router as tasks_routes

from users.routes import router as users_routes

from pages.routes import router as pages_routes

import time


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
    print("Application startup")
    yield
    print("Application shutdown")


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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    print(exc.__dict__)
    error_response = {
        "error": True,
        "status_code": exc.status_code,
        "detail": exc.detail
    }
    return JSONResponse(status_code =exc.status_code, content=error_response)

@app.exception_handler(RequestValidationError)
async def http_validation_handler(request, exc):
    print(exc.__dict__)
    error_response = {
        "error": True,
        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "detail": exc.errors()
    }
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_response)
