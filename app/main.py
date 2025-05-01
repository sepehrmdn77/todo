from fastapi import FastAPI
from contextlib import asynccontextmanager
from tasks.routes import router as tasks_routes

tags_metadata=[
    {
        "name" : "tasks",
        "description" : "Operations related to task management",
        "externalDocs" : {
            "description" : "More about tasks",
            "url" : "https://example.com/docs/tasks"
        }

    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup")
    yield
    print("Application shutdown")

app = FastAPI(lifespan=lifespan, openapi_tags=tags_metadata,   title="Todo App",
    description="Simple todo app for testing purpose",
    summary="Deadpool's favorite app. Nuff said.",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },)

app.include_router(tasks_routes)
