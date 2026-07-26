"""Build and send the daily digest email via Gmail SMTP."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


@dataclass
class NewFigure:
    code: str
    name: str
    url: str
    status: str
    brand: str | None = None
    price_jpy: int | None = None
    release_date: str | None = None


def _format_figure_text(fig: NewFigure) -> str:
    lines = [f"- {fig.name} [{fig.code}]"]
    details = []
    if fig.brand:
        details.append(fig.brand)
    if fig.price_jpy:
        details.append(f"¥{fig.price_jpy:,}")
    if fig.release_date:
        details.append(f"Release: {fig.release_date}")
    if fig.status == "futurerelease":
        details.append("PREORDER")
    if details:
        lines.append("  " + " | ".join(details))
    lines.append(f"  {fig.url}")
    return "\n".join(lines)


def _format_figure_html(fig: NewFigure) -> str:
    details = []
    if fig.brand:
        details.append(fig.brand)
    if fig.price_jpy:
        details.append(f"¥{fig.price_jpy:,}")
    if fig.release_date:
        details.append(f"Release: {fig.release_date}")
    if fig.status == "futurerelease":
        details.append("<b>PREORDER</b>")
    details_html = " | ".join(details)
    return (
        "<li>"
        f'<a href="{fig.url}">{fig.name}</a> <span style="color:#888">[{fig.code}]</span>'
        f"<br>{details_html}"
        "</li>"
    )


def build_new_items_email(new_figures: list[NewFigure]) -> tuple[str, str, str]:
    """Returns (subject, plain_text_body, html_body)."""
    subject = f"HLJ Pokemon figures: {len(new_figures)} new listing(s)"
    text_body = "New Pokemon Moncolle / Monster Collection listings on HLJ.com:\n\n" + "\n\n".join(
        _format_figure_text(fig) for fig in new_figures
    )
    html_body = (
        "<p>New Pokemon Moncolle / Monster Collection listings on HLJ.com:</p><ul>"
        + "".join(_format_figure_html(fig) for fig in new_figures)
        + "</ul>"
    )
    return subject, text_body, html_body


def build_baseline_email(item_count: int) -> tuple[str, str, str]:
    subject = "Pokemon figure tracker initialized"
    text_body = (
        f"Baseline recorded: {item_count} existing HLJ.com listings are now tracked as seen.\n"
        "From tomorrow onward you'll only be emailed about genuinely new listings."
    )
    html_body = f"<p>{text_body}</p>"
    return subject, text_body, html_body


def send_email(
    subject: str,
    text_body: str,
    html_body: str,
    gmail_address: str,
    app_password: str,
) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = gmail_address
    message["To"] = gmail_address
    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(gmail_address, app_password)
        server.sendmail(gmail_address, [gmail_address], message.as_string())
