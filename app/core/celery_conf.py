from celery import Celery
from core.config import settings
import time
import datetime

celery_app = Celery(
    'worker',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BACKEND_URL
)

celery_app.conf.update(
    broker_connection_retry_on_startup=True # adding this line to avoid warning
)

celery_app.conf.update(
    timezone="UTC",
    beat_schedule={
        "print-hello-every-minute": {
            "task": "core.celery_conf.print_hello",
            "schedule": 60.0 # every minute
        }
    }
)

@celery_app.task
def add_number(x,y):
    time.sleep(10)
    return x+y

@celery_app.task
def print_hello():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Hello! current time: {now}")
    