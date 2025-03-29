from celery import Celery,Task
from flask import Flask
from dotenv import load_dotenv
import os

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)

    # Use conf.update to load settings
    celery_app.conf.update(
        broker_url=os.getenv("CELERY_BROKER_URL"),
        result_backend=os.getenv("CELERY_RESULT_BACKEND"),
        timezone=os.getenv("TIMEZONE", "UTC"),
        task_serializer="json",
        accept_content=["json"],
    )

    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
