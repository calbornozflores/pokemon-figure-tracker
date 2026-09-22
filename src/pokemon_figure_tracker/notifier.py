"""Build and send the daily digest email via Gmail SMTP."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .scraper import PAGES_PER_KEYWORD, SEARCH_KEYWORDS

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
    image_bytes: bytes | None = None


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


def _format_figure_html(fig: NewFigure, cid: str | None) -> str:
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
    image_cell = (
        f'<img src="cid:{cid}" width="110" style="display:block;border:1px solid #ddd;">'
        if cid
        else ""
    )
    return (
        '<table cellpadding="0" cellspacing="0" style="margin-bottom:16px;"><tr>'
        f'<td width="120" valign="top">{image_cell}</td>'
        '<td style="padding-left:12px;" valign="top">'
        f'<a href="{fig.url}"><b>{fig.name}</b></a> <span style="color:#888">[{fig.code}]</span>'
        f"<br>{details_html}"
        "</td></tr></table>"
    )


def build_new_items_email(new_figures: list[NewFigure]) -> tuple[str, str, MIMEMultipart]:
    """Returns (subject, plain_text_body, message). message has no From/To yet."""
    subject = f"HLJ Pokemon figures: {len(new_figures)} new listing(s)"
    text_body = "New Pokemon Moncolle / Monster Collection listings on HLJ.com:\n\n" + "\n\n".join(
        _format_figure_text(fig) for fig in new_figures
    )

    cids = [f"fig{i}" if fig.image_bytes else None for i, fig in enumerate(new_figures)]
    html_body = "<p>New Pokemon Moncolle / Monster Collection listings on HLJ.com:</p>" + "".join(
        _format_figure_html(fig, cid) for fig, cid in zip(new_figures, cids)
    )

    message = MIMEMultipart("related")
    message["Subject"] = subject
    alternative = MIMEMultipart("alternative")
    alternative.attach(MIMEText(text_body, "plain"))
    alternative.attach(MIMEText(html_body, "html"))
    message.attach(alternative)

    for fig, cid in zip(new_figures, cids):
        if cid:
            image = MIMEImage(fig.image_bytes)
            image.add_header("Content-ID", f"<{cid}>")
            image.add_header("Content-Disposition", "inline", filename=f"{fig.code}.jpg")
            message.attach(image)

    return subject, text_body, message


def build_baseline_email(item_count: int) -> tuple[str, str, MIMEMultipart]:
    subject = "Pokemon figure tracker initialized"
    text_body = (
        f"Baseline recorded: {item_count} existing HLJ.com listings are now tracked as seen.\n"
        "From tomorrow onward you'll only be emailed about genuinely new listings."
    )
    html_body = f"<p>{text_body}</p>"

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    return subject, text_body, message


def build_heartbeat_email(
    tracked_count: int,
    scraped_count: int,
    last_find_date: str | None,
    last_find_count: int,
) -> tuple[str, str, MIMEMultipart]:
    """Weekly "still alive" mail, sent even when there is nothing new.

    A quiet day and a day the workflow never ran look identical from the inbox - that is
    how a month of skipped runs went unnoticed. With this, a week of total silence is
    itself the alarm.
    """
    subject = "HLJ tracker weekly check-in"
    if last_find_date:
        last_line = f"Last new find: {last_find_date} ({last_find_count} item(s))."
    else:
        last_line = "No new find recorded yet."
    text_body = "\n".join(
        [
            "0 new listings today.",
            f"{tracked_count} products tracked.",
            last_line,
            f"Scraped {scraped_count} listings across "
            f"{len(SEARCH_KEYWORDS)} keywords, {PAGES_PER_KEYWORD} pages each.",
            "",
            "This is the weekly check-in - it means the tracker is running. If a whole",
            "week goes by with no mail at all, something is broken.",
        ]
    )
    html_body = "<p>" + text_body.replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    return subject, text_body, message


def send_email(message: MIMEMultipart, gmail_address: str, app_password: str) -> None:
    message["From"] = gmail_address
    message["To"] = gmail_address

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(gmail_address, app_password)
        server.sendmail(gmail_address, [gmail_address], message.as_string())
