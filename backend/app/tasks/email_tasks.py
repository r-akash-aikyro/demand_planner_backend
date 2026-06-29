from app.tasks.celery_app import celery_app
from app.email.sender import send_email, render


@celery_app.task(name="email.notify")
def notify(to: str, template: str, **kw):
    subject, body = render(template, **kw)
    send_email(to, subject, body)
