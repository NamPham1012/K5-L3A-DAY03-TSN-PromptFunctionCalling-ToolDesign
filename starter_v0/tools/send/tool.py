from __future__ import annotations

import os
import re
from typing import Any

import requests

from tools._shared import TIMEOUT, err, fold_text

# Whole-reply confirmations (accent-folded). Anything else - including "có điều chỉnh"
# or "ok nhưng sửa..." - is NOT treated as consent.
AFFIRMATIVE = {
    "yes", "y", "ok", "okay", "oke", "sure", "confirm", "confirmed", "send", "send it", "post it",
    "co", "u", "uh", "vang", "da", "duoc", "dong y", "xac nhan", "chac chan",
    "gui", "gui di", "dang", "dang di", "dang len", "co gui di", "co dang di", "ok gui di", "ok dang di",
}
NEGATION = re.compile(r"\b(khong|ko|k|dung|huy|chua|no|not|dont|cancel|stop|sua|doi)\b")
TOOL_RESULTS_PREFIX = "TOOL_RESULTS_JSON"


def _confirmation_question(text: str) -> str:
    return f"Bạn xác nhận gửi nội dung sau lên Telegram? (có/không)\n\n---\n{text}\n---"


def is_affirmative(reply: str | None) -> bool:
    folded = fold_text(reply or "")
    folded = re.sub(r"[^a-z0-9 ]+", " ", folded)
    folded = " ".join(folded.split())
    if not folded or NEGATION.search(folded):
        return False
    return folded in AFFIRMATIVE


def latest_user_text(messages: list[dict[str, Any]] | None) -> str | None:
    """Last message the human typed (skips tool-result messages the harness injects as role=user)."""
    for message in reversed(messages or []):
        content = str(message.get("content") or "")
        if message.get("role") == "user" and not content.startswith(TOOL_RESULTS_PREFIX):
            return content
    return None


def guard_send_call(args: dict[str, Any], messages: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    """Code-level confirmation gate. Returns a blocking result, or None if the send may proceed.

    The model sets `confirmed` itself, so the flag alone is not consent. We additionally
    require that the user's latest message is an explicit yes.
    """
    if not args.get("confirmed"):
        return None  # send_telegram itself returns needs_confirmation
    if is_affirmative(latest_user_text(messages)):
        return None
    text = str(args.get("text") or "")
    return {
        "tool": "send_telegram",
        "status": "blocked_needs_user_confirmation",
        "message": "confirmed=true but the user's latest message is not an explicit yes. Nothing was sent.",
        "awaiting_user": True,
        "response_type": "yes_no",
        "question": _confirmation_question(text),
    }


def send_telegram(text: str = "", confirmed: bool = False) -> dict[str, Any]:
    if not (text or "").strip():
        return {"tool": "send_telegram", "error": "ValueError", "message": "text must not be empty"}
    if confirmed is not True:  # "true", 1, "yes" from a sloppy model are not consent
        return {
            "tool": "send_telegram",
            "status": "needs_confirmation",
            "message": "Not sent. Show the draft and ask the user for explicit yes/no confirmation.",
            "awaiting_user": True,
            "response_type": "yes_no",
            "question": _confirmation_question(text),
        }
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            raise RuntimeError("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env var")
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return {"tool": "send_telegram", "status": "sent"}
    except Exception as exc:
        return err("send_telegram", exc)
