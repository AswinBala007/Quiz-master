from celery import Celery,Task
from flask import Flask
from dotenv import load_dotenv
import os
from celery.schedules import crontab

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
        # Configure the schedule for tasks
        beat_schedule={
            # 'send-daily-reminders': {
            #     'task': 'jobs.tasks.send_daily_reminders',
            #     'schedule': crontab(minute='*/10'),  # Run every 10 minutes to catch all user preferences
            #     'options': {'expires': 900}  # Expires after 15 minutes (900 seconds)
            # },
            'send-monthly-reports': {
                'task': 'jobs.tasks.send_monthly_activity_report',
                'schedule': crontab(day_of_month='30', hour='15', minute='34'),  # Run at 9:00 AM on the 1st day of each month
                'options': {'expires': 3600}  # Expires after 1 hour (3600 seconds)
            }
        }
    )

    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
