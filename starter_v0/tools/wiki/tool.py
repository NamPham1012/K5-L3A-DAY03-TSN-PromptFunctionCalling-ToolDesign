from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, clamp_int, err

HEADERS = {"User-Agent": "ResearchAgentToolEval/0.1 (lab exercise)"}
LANGS = {"en", "vi"}


def wiki_search(query: str = "", lang: str = "en", max_results: int = 3) -> dict[str, Any]:
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        lang = lang if lang in LANGS else "en"
        limit = clamp_int(max_results, default=3, high=10)
        response = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": limit,
                "prop": "extracts|info",
                "exintro": 1,
                "explaintext": 1,
                "exsentences": 4,
                "inprop": "url",
                "redirects": 1,
            },
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        pages = (response.json().get("query") or {}).get("pages") or {}
        ordered = sorted(pages.values(), key=lambda page: page.get("index", 0))
        items = [{
            "title": page.get("title"),
            "url": page.get("fullurl") or f"https://{lang}.wikipedia.org/?curid={page.get('pageid')}",
            "source": f"{lang}.wikipedia.org",
            "summary": (page.get("extract") or "").strip(),
        } for page in ordered]
        return {"tool": "wiki_search", "query": query, "lang": lang, "items": items}
    except Exception as exc:
        return err("wiki_search", exc)
