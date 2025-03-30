from celery import Celery
from celery.schedules import crontab
from flask import current_app as app
from tasks import email_reminder

celery_app = app.extensions['celery']
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, email_reminder.s('user@example.com',
                            'reminder to login', 
                            '<h1> hello everyone </h1>'))

    sender.add_periodic_task(
        crontab(hour=14, minute=15, day_of_week='sunday'),
          email_reminder.s('user@example.com',
                            'reminder to login', 
                            '<h1> hello everyone </h1>')
                            ,name = 'weekly reminder' )
@celery_app.task
def test(arg):
    print(arg)

@celery_app.task
def add(x, y):
    z = x + y
    print(z)