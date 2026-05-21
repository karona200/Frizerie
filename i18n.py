import json
import os
from functools import lru_cache
from fastapi import Request

SUPPORTED       = ["ro", "en", "de", "fr", "es", "it", "hu", "tr", "ru", "pl"]
ADMIN_SUPPORTED = ["ro", "en", "de", "tr"]
DEFAULT         = "ro"


@lru_cache(maxsize=None)
def _load(lang: str) -> dict:
    path = os.path.join("translations", f"{lang}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def detect_lang(request: Request) -> str:
    lang = request.cookies.get("lang", "")
    if lang in SUPPORTED:
        return lang
    accept = request.headers.get("Accept-Language", "")
    for part in accept.split(","):
        code = part.strip().split(";")[0].split("-")[0].lower()
        if code in SUPPORTED:
            return code
    return DEFAULT


def get_t(request: Request) -> tuple[dict, str]:
    lang = detect_lang(request)
    t = dict(_load(DEFAULT))
    t.update(_load(lang))
    return t, lang


def get_admin_t(request: Request) -> tuple[dict, str]:
    lang = detect_lang(request)
    if lang not in ADMIN_SUPPORTED:
        lang = DEFAULT
    t = dict(_load(DEFAULT))
    t.update(_load(lang))
    return t, lang
