from celery import Celery
from core.config import settings

celery_app = Celery(
    'worker',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BACKEND_URL
)

@celery_app.task
def add_number(x,y):
    return x+y
