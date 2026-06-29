import smtplib
from email.mime.text import MIMEText
from app.core.config import settings


def send_email(to: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            if settings.SMTP_USER:
                s.starttls()
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.sendmail(settings.SMTP_FROM, [to], msg.as_string())
    except Exception as e:  # noqa: BLE001 — email failures shouldn't break flows
        print(f"[email] send failed to {to}: {e}")


TEMPLATES = {
    "forecast_ready": ("Forecast {version} ready for approval",
                       "<p>Forecast <b>{version}</b> is ready.</p><p>{summary}</p>"),
    "override_pending": ("Override for {product} needs approval",
                         "<p>Override on <b>{product}</b>: {original} → {override} "
                         "({pct}%).</p><p>Reason: {reason}</p>"),
    "override_decided": ("Your override was {status}",
                         "<p>Your override on <b>{product}</b> was <b>{status}</b>.</p>"
                         "<p>{notes}</p>"),
    "forecast_published": ("New forecast published",
                           "<p>Forecast <b>{version}</b> has been published.</p>"),
}


def render(template: str, **kw) -> tuple[str, str]:
    subj, body = TEMPLATES[template]
    return subj.format(**kw), body.format(**kw)
