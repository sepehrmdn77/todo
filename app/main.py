# from auth.basic_auth import get_authenticated_user

from auth.jwt_auth import get_authenticated_user

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends

from tasks.routes import router as tasks_routes

from users.routes import router as users_routes

from users.models import UsersModel

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


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

from fastapi.security import APIKeyHeader

header_scheme = APIKeyHeader(name="x-key")

@app.get("/public", tags=["Auth Test"])
def public_route():
    return {"message": "This is a public route"}

@app.get("/private", tags=["Auth Test"]) # Token authentication
def private_route(user: HTTPAuthorizationCredentials= Depends(get_authenticated_user)):
    print(user.username)
    
    return {"message": "This is a private page"}

# @app.get("/private", tags=["Auth Test"]) # Http authorize
# def private_route(credentials: HTTPAuthorizationCredentials= Depends(security)):
#     print(credentials)
#     return {"message": "This is a private page"}

# @app.get("/private", tags=["Auth Test"]) # Old basic user pass method
# def private_route(user: UsersModel = Depends(get_authenticated_user)):
#     print(user)
#     return {"message": "This is a private page"}

# @app.get("/private", tags=["Auth Test"]) # APIkey Header auth
# def private_route(api_key = Depends(header_scheme)):
#     print(api_key)
#     return {"message": "This is a private page"}

# from fastapi.security import APIKeyQuery

# query_scheme = APIKeyQuery(name="api_key")

# @app.get("/private", tags=["Auth Test"]) # APIkey Query auth
# def private_route(api_key = Depends(header_scheme)):
#     print(api_key)
#     return {"message": "This is a private page"}